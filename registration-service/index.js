const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const connectDB = require('./db');
const Person = require('./person.schema');

const app = express();
app.use(express.json());
app.use(cors());

connectDB();

// Registration Endpoint
// Accessible via Gateway: POST http://<gateway-host>:4000/register/userregister
app.post('/userregister', async (req, res) => {
  const { name, emailid, pass, mobile, role } = req.body;

  // Validate required fields
  if (!name || !emailid || !pass || !mobile) {
    return res.status(400).json({ 
      message: 'Please provide all required fields: name, emailid, pass, mobile' 
    });
  }

  try {
    // Check if user already exists with the given email
    const existingPerson = await Person.findOne({ emailid });
    if (existingPerson) {
      return res.status(400).json({ 
        message: 'Email already registered. Duplicate accounts are not allowed.' 
      });
    }

    // Hash password before saving to DB
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(pass, salt);

    // Create new Person record
    const newPerson = new Person({
      name,
      emailid,
      pass: hashedPassword,
      mobile,
      role: role || 'user', // Defaults to 'user'
    });

    await newPerson.save();

    res.status(201).json({
      message: 'Account registered successfully',
      user: {
        _id: newPerson._id,
        name: newPerson.name,
        emailid: newPerson.emailid,
        mobile: newPerson.mobile,
        role: newPerson.role
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Fixed Port: Set to 5001 to align with your API Gateway configuration
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Register Service running on port ${PORT}`));