const express = require('express');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const Person = require('./person.schema');

const app = express();
app.use(express.json());
app.use(cors());

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

function requireInternalKey(req, res, next) {
  if (!process.env.INTERNAL_API_KEY || req.get('x-internal-api-key') !== process.env.INTERNAL_API_KEY) {
    return res.status(401).json({ message: 'Invalid internal API key' });
  }
  next();
}

app.post('/internal/users', requireInternalKey, async (req, res) => {
  const { name, emailid, pass, mobile, role = 'user' } = req.body || {};
  if (!name || !emailid || !pass || !mobile || !['user', 'admin'].includes(role)) {
    return res.status(400).json({ message: 'Provide name, emailid, pass, mobile, and a valid role' });
  }
  if (await Person.findOne({ emailid })) return res.status(409).json({ message: 'Email already registered' });
  const person = new Person({ name, emailid, pass: await bcrypt.hash(pass, await bcrypt.genSalt(10)), mobile, role, active: true });
  await person.save();
  return res.status(201).json({ id: String(person._id), name: person.name, emailid: person.emailid, mobile: person.mobile, role: person.role, active: person.active });
});

app.patch('/internal/users/:id', requireInternalKey, async (req, res) => {
  const allowed = ['name', 'emailid', 'mobile', 'role', 'active'];
  const updates = Object.fromEntries(Object.entries(req.body || {}).filter(([key]) => allowed.includes(key)));
  if (!Object.keys(updates).length || (updates.role && !['user', 'admin'].includes(updates.role))) {
    return res.status(400).json({ message: 'Provide valid account updates' });
  }
  try {
    const person = await Person.findByIdAndUpdate(req.params.id, { $set: updates }, { new: true, runValidators: true });
    if (!person) return res.status(404).json({ message: 'Account not found' });
    return res.json({ id: String(person._id), name: person.name, emailid: person.emailid, mobile: person.mobile, role: person.role, active: person.active });
  } catch (error) {
    return res.status(400).json({ message: error.code === 11000 ? 'Email already registered' : 'Invalid account update' });
  }
});

app.post('/', async (req, res) => {
    const { name, emailid, pass, mobile } = req.body;
  if (!name || !emailid || !pass || !mobile) return res.status(400).json({ message: 'Please provide all required fields: name, emailid, pass, mobile' });

  try {
    if (await Person.findOne({ emailid })) return res.status(400).json({ message: 'Email already registered. Duplicate accounts are not allowed.' });
    const hashedPassword = await bcrypt.hash(pass, await bcrypt.genSalt(10));
    const newPerson = new Person({ name, emailid, pass: hashedPassword, mobile, role: 'user', active: true });
    await newPerson.save();
    res.status(201).json({ message: 'Account registered successfully', user: { _id: newPerson._id, name: newPerson.name, emailid: newPerson.emailid, mobile: newPerson.mobile, role: newPerson.role } });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

module.exports = app;
