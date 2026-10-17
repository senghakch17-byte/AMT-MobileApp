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

async function request(path, token) {
  const response = await fetch(`${url}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  upstream = http.createServer((req, res) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ path: req.url, method: req.method })); });
  await listen(upstream);
  const target = `http://127.0.0.1:${upstream.address().port}`;
  process.env.REGISTER_SERVICE_URL = target; process.env.LOGIN_SERVICE_URL = target; process.env.REQUEST_SERVICE_URL = target; process.env.EVENT_SERVICE_URL = target; process.env.ATTENDANCE_SERVICE_URL = target; process.env.NOTIFICATION_SERVICE_URL = target; process.env.MEMBER_SERVICE_URL = target; process.env.LIBRARY_SERVICE_URL = target;
  const app = require('../app');
  appServer = app.listen(0);
  await new Promise((resolve) => appServer.once('listening', resolve));
  url = `http://127.0.0.1:${appServer.address().port}`;
});
test.after(async () => Promise.all([new Promise((resolve) => appServer.close(resolve)), new Promise((resolve) => upstream.close(resolve))]));

test('health and public routes work through proxy', async () => {
  assert.deepEqual(await request('/health'), { status: 200, body: { status: 'ok' } });
  assert.deepEqual(await request('/auth/login'), { status: 200, body: { path: '/login', method: 'GET' } });
});

test('protected routes reject bad tokens and proxy valid JWT', async () => {
  assert.equal((await request('/request/api/v1/health')).status, 401);
  assert.equal((await request('/request/api/v1/health', 'bad')).status, 401);
  const token = jwt.sign({ id: 'user-1', emailid: 'user@example.com', role: 'user' }, process.env.JWT_SECRET);
  assert.deepEqual(await request('/request/api/v1/health', token), { status: 200, body: { path: '/api/v1/health', method: 'GET' } });
});