const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const jwt = require('jsonwebtoken');

process.env.JWT_SECRET = 'gateway-test-secret';
let upstream;
let appServer;
let url;

function listen(server) {
  return new Promise((resolve) => { server.listen(0, '127.0.0.1', resolve); });
}

async function request(path, token, method = 'GET') {
  const response = await fetch(`${url}${path}`, { method, headers: token ? { Authorization: `Bearer ${token}` } : {} });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  upstream = http.createServer((req, res) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ path: req.url, method: req.method })); });
  await listen(upstream);
  const target = `http://127.0.0.1:${upstream.address().port}`;
  process.env.REGISTER_SERVICE_URL = target; process.env.LOGIN_SERVICE_URL = target; process.env.REQUEST_SERVICE_URL = target; process.env.ANNOUNCEMENT_SERVICE_URL = target; process.env.ATTENDANCE_SERVICE_URL = target; process.env.NOTIFICATION_SERVICE_URL = target; process.env.USER_SERVICE_URL = target; process.env.BOOKING_SERVICE_URL = target;
  const app = require('../app');
  appServer = app.listen(0);
  await new Promise((resolve) => appServer.once('listening', resolve));
  url = `http://127.0.0.1:${appServer.address().port}`;
});
test.after(async () => Promise.all([new Promise((resolve) => appServer.close(resolve)), new Promise((resolve) => upstream.close(resolve))]));

test('health and public routes work through proxy', async () => {
  const health = await request('/health');
  assert.equal(health.status, 200);
  assert.equal(health.body.status, 'ok');
  assert.equal(typeof health.body.instance, 'string');
  assert.deepEqual(await request('/login'), { status: 200, body: { path: '/', method: 'GET' } });
});

test('protected routes reject bad tokens and proxy valid JWT', async () => {
  for (const prefix of ['request', 'announcement', 'attendance', 'notification', 'user', 'booking']) {
    assert.deepEqual(await request(`/${prefix}/health`), { status: 200, body: { path: '/health', method: 'GET' } });
  }
  assert.equal((await request('/request/anything')).status, 401);
  const token = jwt.sign({ id: 'user-1', emailid: 'user@example.com', role: 'user' }, process.env.JWT_SECRET);
  assert.deepEqual(await request('/request/anything', token), { status: 200, body: { path: '/anything', method: 'GET' } });
});

test('gateway forwards authenticated users and services enforce roles', async () => {
  const user = jwt.sign({ id: 'user-1', emailid: 'user@example.com', role: 'user' }, process.env.JWT_SECRET);
  const admin = jwt.sign({ id: 'admin-1', emailid: 'admin@example.com', role: 'admin' }, process.env.JWT_SECRET);
  assert.deepEqual(await request('/announcement', user, 'POST'), { status: 200, body: { path: '/', method: 'POST' } });
  assert.deepEqual(await request('/announcement', admin, 'POST'), { status: 200, body: { path: '/', method: 'POST' } });
  assert.deepEqual(await request('/attendance/', user), { status: 200, body: { path: '/', method: 'GET' } });
  assert.deepEqual(await request('/attendance/attendance-1', user, 'PATCH'), { status: 200, body: { path: '/attendance-1', method: 'PATCH' } });
  assert.deepEqual(await request('/attendance/attendance-1', admin, 'PATCH'), { status: 200, body: { path: '/attendance-1', method: 'PATCH' } });
  assert.deepEqual(await request('/booking/rooms', user), { status: 200, body: { path: '/rooms', method: 'GET' } });
  assert.deepEqual(await request('/booking/rooms', user, 'POST'), { status: 200, body: { path: '/rooms', method: 'POST' } });
  assert.deepEqual(await request('/booking/rooms', admin, 'POST'), { status: 200, body: { path: '/rooms', method: 'POST' } });
  assert.deepEqual(await request('/booking/booking-1/approve', user, 'POST'), { status: 200, body: { path: '/booking-1/approve', method: 'POST' } });
  assert.deepEqual(await request('/booking/booking-1/approve', admin, 'POST'), { status: 200, body: { path: '/booking-1/approve', method: 'POST' } });
});
