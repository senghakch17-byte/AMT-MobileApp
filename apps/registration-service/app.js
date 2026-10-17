const express = require('express');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const Person = require('./person.schema');

const app = express();
app.use(express.json());
app.use(cors());

app.post('/register', async (req, res) => {
  const { name, emailid, pass, mobile, role } = req.body;
  if (!name || !emailid || !pass || !mobile) return res.status(400).json({ message: 'Please provide all required fields: name, emailid, pass, mobile' });

  try {
    if (await Person.findOne({ emailid })) return res.status(400).json({ message: 'Email already registered. Duplicate accounts are not allowed.' });
    const hashedPassword = await bcrypt.hash(pass, await bcrypt.genSalt(10));
    const newPerson = new Person({ name, emailid, pass: hashedPassword, mobile, role: role || 'user' });
    await newPerson.save();
    res.status(201).json({ message: 'Account registered successfully', user: { _id: newPerson._id, name: newPerson.name, emailid: newPerson.emailid, mobile: newPerson.mobile, role: newPerson.role } });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

module.exports = app;