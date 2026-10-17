const test = require('node:test');
const assert = require('node:assert/strict');
const jwt = require('jsonwebtoken');

process.env.JWT_SECRET = 'login-test-secret';
const app = require('../app');
const Person = require('../person.schema');
const bcrypt = require('bcryptjs');
const originalFindOne = Person.findOne;
const originalCompare = bcrypt.compare;
let server;
let url;

async function request(body) {
  const response = await fetch(`${url}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  url = `http://127.0.0.1:${server.address().port}`;
});
test.after(async () => {
  Person.findOne = originalFindOne;
  bcrypt.compare = originalCompare;
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
});
test.beforeEach(() => { Person.findOne = originalFindOne; bcrypt.compare = originalCompare; });

test('login validates credentials and handles lookup failures', async () => {
  assert.deepEqual(await request({}), { status: 400, body: { message: 'Please provide emailid, pass, and role' } });
  Person.findOne = async () => null;
  assert.deepEqual(await request({ emailid: 'user@example.com', pass: 'secret', role: 'user' }), { status: 400, body: { message: 'Invalid credentials' } });
  Person.findOne = async () => { throw new Error('database unavailable'); };
  assert.deepEqual(await request({ emailid: 'user@example.com', pass: 'secret', role: 'user' }), { status: 500, body: { message: 'Server error', error: 'database unavailable' } });
});

test('login rejects role mismatch and invalid password', async () => {
  Person.findOne = async () => ({ role: 'admin', pass: 'hash' });
  assert.deepEqual(await request({ emailid: 'user@example.com', pass: 'secret', role: 'user' }), { status: 403, body: { message: 'Access denied: Role mismatch' } });
  Person.findOne = async () => ({ role: 'user', pass: 'hash' });
  bcrypt.compare = async () => false;
  assert.deepEqual(await request({ emailid: 'user@example.com', pass: 'secret', role: 'user' }), { status: 400, body: { message: 'Invalid credentials' } });
});

test('login returns JWT with database identity', async () => {
  Person.findOne = async () => ({ _id: 'user-1', name: 'User', emailid: 'user@example.com', role: 'user', pass: 'hash' });
  bcrypt.compare = async () => true;
  const response = await request({ emailid: 'user@example.com', pass: 'secret', role: 'user' });
  assert.equal(response.status, 200);
  assert.deepEqual(response.body.user, { _id: 'user-1', name: 'User', emailid: 'user@example.com', role: 'user' });
  assert.deepEqual(jwt.verify(response.body.token, process.env.JWT_SECRET), { id: 'user-1', emailid: 'user@example.com', role: 'user', iat: jwt.decode(response.body.token).iat, exp: jwt.decode(response.body.token).exp });
});