const assert = require('node:assert/strict');
const test = require('node:test');
const jwt = require('jsonwebtoken');

process.env.MONGO_URI = 'mongodb://127.0.0.1:27017/notification-test';
process.env.JWT_SECRET = 'notification-test-secret';

const app = require('../app');
const Notification = require('../models/notification.model');
const NotificationPreference = require('../models/preference.model');
const NotificationReceipt = require('../models/notificationReceipt.model');

const notificationId = '507f1f77bcf86cd799439011';
let server;
let url;

function token(claims = {}) {
  return jwt.sign({ id: 'user-1', role: 'user', ...claims }, process.env.JWT_SECRET, { algorithm: 'HS256' });
}

async function request(path, { method = 'GET', auth = token() } = {}) {
  const response = await fetch(`${url}${path}`, {
    method,
    headers: auth ? { Authorization: `Bearer ${auth}` } : {},
  });
  return { status: response.status, body: response.status === 204 ? null : await response.json() };
}

test.before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  url = `http://127.0.0.1:${server.address().port}`;
});

test.after(async () => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));

test('receipt schema and user mutations keep role notifications shared', async () => {
  assert.equal(Notification.schema.path('readAt'), undefined);
  assert.deepEqual(
    NotificationReceipt.schema.indexes().find(([fields]) => fields.notificationId === 1 && fields.userId === 1),
    [{ notificationId: 1, userId: 1 }, { unique: true }],
  );

  const originals = {
    aggregate: Notification.aggregate,
    preferenceFindOne: NotificationPreference.findOne,
    receiptFindOneAndUpdate: NotificationReceipt.findOneAndUpdate,
    receiptBulkWrite: NotificationReceipt.bulkWrite,
  };
  const receiptUpdates = [];
  let bulkOperations;
  NotificationPreference.findOne = async () => null;
  Notification.aggregate = async (pipeline) => {
    if (pipeline.some((stage) => stage.$project?._id === 1)) return [{ _id: notificationId }];
    return [{ id: notificationId, type: 'event.published', readAt: null }];
  };
  NotificationReceipt.findOneAndUpdate = async (filter, update) => {
    receiptUpdates.push({ filter, update });
    return { readAt: new Date('2026-10-17T00:00:00.000Z') };
  };
  NotificationReceipt.bulkWrite = async (operations) => { bulkOperations = operations; };

  try {
    const read = await request(`/api/v1/notifications/${notificationId}/read`, { method: 'PATCH' });
    assert.equal(read.status, 200);
    assert.deepEqual(receiptUpdates[0].filter, { notificationId, userId: 'user-1' });
    assert.equal(receiptUpdates[0].update.$setOnInsert.deletedAt, null);

    const otherUserRead = await request(`/api/v1/notifications/${notificationId}/read`, {
      method: 'PATCH', auth: token({ id: 'user-2' }),
    });
    assert.equal(otherUserRead.status, 200);
    assert.deepEqual(receiptUpdates[1].filter, { notificationId, userId: 'user-2' });

    const all = await request('/api/v1/notifications/read-all', { method: 'PATCH' });
    assert.deepEqual(all, { status: 200, body: { markedRead: 1 } });
    assert.equal(bulkOperations[0].updateOne.filter.userId, 'user-1');
    assert.equal(bulkOperations[0].updateOne.filter.notificationId, notificationId);

    const deleted = await request(`/api/v1/notifications/${notificationId}`, { method: 'DELETE' });
    assert.equal(deleted.status, 204);
    assert.deepEqual(receiptUpdates[2].filter, { notificationId, userId: 'user-1' });
    assert.ok(receiptUpdates[2].update.$set.deletedAt instanceof Date);
  } finally {
    Object.assign(Notification, { aggregate: originals.aggregate });
    Object.assign(NotificationPreference, { findOne: originals.preferenceFindOne });
    Object.assign(NotificationReceipt, {
      findOneAndUpdate: originals.receiptFindOneAndUpdate,
      bulkWrite: originals.receiptBulkWrite,
    });
  }
});