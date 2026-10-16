const mongoose = require('mongoose');

async function connectDB() {
  const connection = await mongoose.connect(process.env.MONGO_URI);
  console.log(`MongoDB Connected: ${connection.connection.host}`);
}

async function disconnectDB() {
  await mongoose.disconnect();
}

module.exports = { connectDB, disconnectDB };
