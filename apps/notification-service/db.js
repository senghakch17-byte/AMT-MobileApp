const mongoose = require('mongoose');
const { mongoUri } = require('./config');

async function connectDatabase() {
  mongoose.set('strictQuery', true);
  await mongoose.connect(mongoUri);
  console.log('[Notification] Connected to MongoDB');
}

async function disconnectDatabase() {
  await mongoose.disconnect();
}

module.exports = { connectDatabase, disconnectDatabase };
