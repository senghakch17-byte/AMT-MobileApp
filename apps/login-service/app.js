const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const Person = require('./person.schema');

const app = express();
app.use(express.json());
app.use(cors());

app.post('/login', async (req, res) => {
  const { emailid, pass, role } = req.body;
  if (!emailid || !pass || !role) return res.status(400).json({ message: 'Please provide emailid, pass, and role' });

  try {
    const person = await Person.findOne({ emailid });
    if (!person) return res.status(400).json({ message: 'Invalid credentials' });
    if (person.role !== role) return res.status(403).json({ message: 'Access denied: Role mismatch' });
    if (!await bcrypt.compare(pass, person.pass)) return res.status(400).json({ message: 'Invalid credentials' });

    const token = jwt.sign({ id: person._id, emailid: person.emailid, role: person.role }, process.env.JWT_SECRET, { expiresIn: '1h' });
    res.status(200).json({ message: 'Login successful', user: { _id: person._id, name: person.name, emailid: person.emailid, role: person.role }, token });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

module.exports = app;