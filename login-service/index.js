const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const connectDB = require('./db');
const Person = require('./person.schema');

const app = express();
app.use(express.json());
app.use(cors());

connectDB();

// Fixed Port: 5002 matches the target in your API Gateway
const PORT = process.env.PORT || 5002;

// Login Endpoint
// Accessible via Gateway: POST http://<gateway-host>:4000/auth/login
app.post('/login', async (req, res) => {
  const { emailid, pass, role } = req.body;

  // 1. Validate that role, emailid, and pass are present in request body
  if (!emailid || !pass || !role) {
    return res.status(400).json({ message: 'Please provide emailid, pass, and role' });
  }

  try {
    const person = await Person.findOne({ emailid });
    if (!person) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    // 2. Validate that the requested role matches the user's assigned role in DB
    if (person.role !== role) {
      return res.status(403).json({ message: 'Access denied: Role mismatch' });
    }

    const isMatch = await bcrypt.compare(pass, person.pass);
    if (!isMatch) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    // Sign JWT token using standard process.env.JWT_SECRET
    const token = jwt.sign(
      { id: person._id, emailid: person.emailid, role: person.role },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );

    res.status(200).json({
      message: 'Login successful',
      user: {
        _id: person._id,
        name: person.name,
        emailid: person.emailid,
        role: person.role
      },
      token
    });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

app.listen(PORT, () => console.log(`Authentication Service running on port ${PORT}`));