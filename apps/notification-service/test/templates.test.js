const assert = require('node:assert/strict');
const test = require('node:test');
const { createNotification } = require('../services/templates');

test('builds a direct notification from a supported event', () => {
  const notification = createNotification({
    event_id: 'request:123:approved',
    type: 'request.approved',
    recipient_id: 'student-1',
    data: { request_id: '123' },
  });

  assert.equal(notification.recipientId, 'student-1');
  assert.equal(notification.title, 'Request approved');
  assert.deepEqual(notification.data, { request_id: '123' });
});

test('builds a role-targeted notification', () => {
  const notification = createNotification({
    event_id: 'event:123:published',
    type: 'event.published',
    recipient_role: 'user',
  });

  assert.equal(notification.recipientRole, 'user');
  assert.equal(notification.recipientId, undefined);
});

test('rejects an event without a recipient', () => {
  assert.throws(
    () => createNotification({ event_id: 'event:123', type: 'event.published' }),
    /recipient_id or recipient_role/,
  );
});
