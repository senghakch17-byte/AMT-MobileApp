const test = require('node:test');
const assert = require('node:assert/strict');

const app = require('../app');
const Person = require('../person.schema');
const bcrypt = require('bcryptjs');
const originalFindOne = Person.findOne;
const originalSave = Person.prototype.save;
const originalGenSalt = bcrypt.genSalt;
const originalHash = bcrypt.hash;
let server;
let url;

async function request(body) {
  const response = await fetch(`${url}/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  url = `http://127.0.0.1:${server.address().port}`;
});
test.after(async () => {
  Person.findOne = originalFindOne; Person.prototype.save = originalSave; bcrypt.genSalt = originalGenSalt; bcrypt.hash = originalHash;
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
});
test.beforeEach(() => { Person.findOne = originalFindOne; Person.prototype.save = originalSave; bcrypt.genSalt = originalGenSalt; bcrypt.hash = originalHash; });

const valid = { name: 'User', emailid: 'user@example.com', pass: 'secret', mobile: 12345678 };

test('registration validates fields, duplicates, and database failures', async () => {
  assert.equal((await request({})).status, 400);
  Person.findOne = async () => ({ _id: 'existing' });
  assert.deepEqual(await request(valid), { status: 400, body: { message: 'Email already registered. Duplicate accounts are not allowed.' } });
  Person.findOne = async () => { throw new Error('database unavailable'); };
  assert.deepEqual(await request(valid), { status: 500, body: { message: 'Server error', error: 'database unavailable' } });
});

test('registration hashes password, defaults role, and excludes password response', async () => {
  let saved = false;
  Person.findOne = async () => null;
  bcrypt.genSalt = async () => 'salt';
  bcrypt.hash = async (pass, salt) => { assert.equal(pass, 'secret'); assert.equal(salt, 'salt'); return 'hashed'; };
  Person.prototype.save = async function save() { saved = true; };
  const response = await request(valid);
  assert.equal(response.status, 201);
  assert.equal(response.body.message, 'Account registered successfully');
  assert.match(response.body.user._id, /^[a-f0-9]{24}$/);
  assert.deepEqual({ ...response.body.user, _id: undefined }, { _id: undefined, name: 'User', emailid: 'user@example.com', mobile: 12345678, role: 'user' });
  assert.ok(saved);
});

test('registration preserves supplied role', async () => {
  Person.findOne = async () => null;
  Person.prototype.save = async function save() { this._id = 'admin-1'; };
  const response = await request({ ...valid, role: 'admin' });
  assert.equal(response.status, 201);
  assert.equal(response.body.user.role, 'admin');
});