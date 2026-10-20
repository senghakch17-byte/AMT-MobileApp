const test = require('node:test');
const assert = require('node:assert/strict');
const jwt = require('jsonwebtoken');

process.env.JWT_SECRET = 'attendance-test-secret';
const app = require('../app');
const Attendance = require('../models/attendance.model');
const notifications = require('../utils/notifications');
const { parseDateOnly, utcDayStart } = require('../utils/date');
const original = Object.fromEntries(['create', 'findOneAndUpdate', 'exists', 'find', 'findById'].map((key) => [key, Attendance[key]]));
const originalPublishNotification = notifications.publishNotification;
let server;
let url;

function token(claims = {}) {
  return jwt.sign({ id: 'user-1', emailid: 'user@example.com', role: 'user', ...claims }, process.env.JWT_SECRET, { algorithm: 'HS256' });
}

function record(overrides = {}) {
  return {
    _id: '507f1f77bcf86cd799439011', userID: 'user-1', userEmail: 'user@example.com',
    attendanceDate: new Date('2026-10-16T00:00:00.000Z'), checkIn: new Date('2026-10-16T09:00:00.000Z'), checkOut: null, status: 'present',
    save: async () => undefined, ...overrides,
  };
}

function query(records) {
  return {
    sort(sort) { assert.deepEqual(sort, { attendanceDate: -1 }); return this; },
    limit(limit) { assert.equal(limit, 100); return Promise.resolve(records); },
  };
}

async function request(path, { method = 'GET', body, auth } = {}) {
  const response = await fetch(`${url}${path}`, {
    method,
    headers: { ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...(auth === undefined ? {} : { Authorization: `Bearer ${auth}` }) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  url = `http://127.0.0.1:${server.address().port}`;
});
test.after(async () => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
test.beforeEach(() => Object.assign(Attendance, original));
test.afterEach(() => { notifications.publishNotification = originalPublishNotification; });

test('date helpers and schema enforce storage contract', () => {
  assert.equal(utcDayStart(new Date('2026-10-16T18:45:00Z')).toISOString(), '2026-10-16T00:00:00.000Z');
  assert.equal(parseDateOnly('2024-02-29', 'date').toISOString(), '2024-02-29T00:00:00.000Z');
  assert.throws(() => parseDateOnly('2026-02-29', 'date'), /valid YYYY-MM-DD/);
  assert.throws(() => parseDateOnly('16-10-2026', 'date'), /valid YYYY-MM-DD/);
  assert.ok(Attendance.schema.path('userID'));
  assert.equal(Attendance.schema.path('studentId'), undefined);
  assert.deepEqual(Attendance.schema.indexes().find(([fields]) => fields.userID === 1 && fields.attendanceDate === 1), [{ userID: 1, attendanceDate: 1 }, { unique: true }]);
  assert.deepEqual(Attendance.schema.path('status').enumValues, ['present', 'late', 'absent', 'excused']);
});

test('health, unknown routes, and JWT failures return expected responses', async () => {
  assert.deepEqual(await request('/health'), { status: 200, body: { status: 'ok' } });
  assert.deepEqual(await request('/missing', { auth: token() }), { status: 404, body: { message: 'Route not found' } });
  for (const auth of [undefined, 'bad', jwt.sign({ id: 'user-1' }, 'wrong-secret'), token({ exp: 1 }), token({ role: undefined })]) {
    const response = await request('/me', { auth });
    assert.equal(response.status, 401);
  }
});

test('check-in uses JWT identity and maps duplicate records to conflict', async () => {
  let created;
  Attendance.create = async (input) => { created = input; return record(input); };
  const response = await request('/check-in', { method: 'POST', auth: token(), body: { userID: 'forged', userEmail: 'forged@example.com' } });
  assert.equal(response.status, 201);
  assert.equal(created.userID, 'user-1');
  assert.equal(created.userEmail, 'user@example.com');
  assert.equal(created.status, 'present');
  assert.equal(created.attendanceDate.toISOString().slice(11), '00:00:00.000Z');
  Attendance.create = async () => { const error = new Error('duplicate'); error.code = 11000; throw error; };
  assert.deepEqual(await request('/check-in', { method: 'POST', auth: token() }), { status: 409, body: { message: 'Attendance record already exists for this user and date' } });
});

test('check-out handles success, absent check-in, and duplicate check-out', async () => {
  Attendance.findOneAndUpdate = async (filter, update, options) => {
    assert.equal(filter.userID, 'user-1'); assert.equal(filter.checkOut, null); assert.ok(update.$set.checkOut instanceof Date);
    assert.deepEqual(options, { new: true, runValidators: true }); return record({ checkOut: new Date() });
  };
  assert.equal((await request('/check-out', { method: 'POST', auth: token() })).status, 200);
  Attendance.findOneAndUpdate = async () => null;
  Attendance.exists = async () => null;
  assert.deepEqual(await request('/check-out', { method: 'POST', auth: token() }), { status: 404, body: { message: 'No check-in found for today' } });
  Attendance.exists = async () => ({ _id: 'existing' });
  assert.deepEqual(await request('/check-out', { method: 'POST', auth: token() }), { status: 409, body: { message: 'Already checked out today' } });
});

test('history uses JWT identity, valid UTC ranges, and 100-record cap', async () => {
  Attendance.find = (filter) => {
    assert.equal(filter.userID, 'user-1');
    assert.equal(filter.attendanceDate.$gte.toISOString(), '2026-10-01T00:00:00.000Z');
    assert.equal(filter.attendanceDate.$lt.toISOString(), '2026-11-01T00:00:00.000Z');
    return query([record()]);
  };
  assert.equal((await request('/me?from=2026-10-01&to=2026-10-31', { auth: token() })).body.length, 1);
  for (const suffix of ['?from=bad', '?to=2026-02-29']) assert.equal((await request(`/me${suffix}`, { auth: token() })).status, 400);
});

test('admin listing rejects users and applies admin filters', async () => {
  assert.deepEqual(await request('/', { auth: token() }), { status: 403, body: { message: "Access Forbidden: Requires 'admin' permissions" } });
  Attendance.find = (filter) => {
    assert.equal(filter.userID, 'user-2');
    assert.equal(filter.attendanceDate.$gte.toISOString(), '2026-10-01T00:00:00.000Z');
    assert.equal(filter.attendanceDate.$lt.toISOString(), '2026-10-02T00:00:00.000Z');
    return query([]);
  };
  assert.deepEqual(await request('/?userID=user-2&from=2026-10-01&to=2026-10-01', { auth: token({ role: 'admin' }) }), { status: 200, body: [] });
});

test('admin correction validates ID, allowed fields, missing records, values, ordering, and valid changes', async () => {
  const admin = token({ role: 'admin' });
  for (const [path, body] of [['/bad-id', { status: 'late' }], ['/507f1f77bcf86cd799439011', {}], ['/507f1f77bcf86cd799439011', { userID: 'other' }]]) {
    assert.equal((await request(path, { method: 'PATCH', auth: admin, body })).status, 400);
  }
  Attendance.findById = async () => null;
  assert.equal((await request('/507f1f77bcf86cd799439011', { method: 'PATCH', auth: admin, body: { status: 'late' } })).status, 404);
  for (const body of [{ attendanceDate: 'bad' }, { checkIn: 1 }, { checkIn: 'bad' }, { checkOut: 'bad' }, { status: 'unknown' }]) {
    Attendance.findById = async () => record();
    assert.equal((await request('/507f1f77bcf86cd799439011', { method: 'PATCH', auth: admin, body })).status, 400);
  }
  Attendance.findById = async () => record({ checkIn: new Date('2026-10-16T10:00:00Z') });
  assert.equal((await request('/507f1f77bcf86cd799439011', { method: 'PATCH', auth: admin, body: { checkOut: '2026-10-16T09:00:00.000Z' } })).status, 400);
  const attendance = record({ updatedAt: new Date('2026-10-17T09:00:00.000Z') }); let saved = false; attendance.save = async () => { saved = true; };
  let published;
  notifications.publishNotification = async (event) => { published = event; };
  Attendance.findById = async () => attendance;
  const response = await request('/507f1f77bcf86cd799439011', { method: 'PATCH', auth: admin, body: { attendanceDate: '2026-10-17', checkIn: '2026-10-17T09:00:00.000Z', checkOut: null, status: 'late' } });
  assert.equal(response.status, 200);
  assert.equal(attendance.attendanceDate.toISOString(), '2026-10-17T00:00:00.000Z');
  assert.equal(attendance.checkOut, null);
  assert.equal(attendance.status, 'late');
  assert.ok(saved);
  assert.deepEqual(published, {
    event_id: 'attendance-service:507f1f77bcf86cd799439011:corrected:2026-10-17T09:00:00.000Z',
    type: 'attendance.corrected',
    recipient_id: 'user-1',
    data: { attendance_id: '507f1f77bcf86cd799439011', screen: 'attendance-history' },
  });
});

test('Mongoose validation errors return 400', async () => {
  Attendance.findById = async () => record({ save: async () => { const error = new Error('invalid document'); error.name = 'ValidationError'; throw error; } });
  assert.deepEqual(await request('/507f1f77bcf86cd799439011', { method: 'PATCH', auth: token({ role: 'admin' }), body: { status: 'present' } }), { status: 400, body: { message: 'invalid document' } });
});