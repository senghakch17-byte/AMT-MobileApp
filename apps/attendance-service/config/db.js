const mongoose = require('mongoose');
const Attendance = require('../models/attendance.model');

async function migrateAttendanceIndexes() {
  let indexes = [];
  try {
    indexes = await Attendance.collection.indexes();
  } catch (error) {
    if (error.code !== 26) throw error;
  }
  const legacyIndex = indexes.find((index) => (
    index.unique
    && !index.partialFilterExpression
    && index.key.userID === 1
    && index.key.attendanceDate === 1
    && Object.keys(index.key).length === 2
  ));
  if (legacyIndex) await Attendance.collection.dropIndex(legacyIndex.name);
  await Attendance.collection.createIndex(
    { userID: 1, attendanceDate: 1 },
    {
      name: 'one_open_attendance_session_per_user_day',
      unique: true,
      partialFilterExpression: { checkOut: null, deletedAt: null },
    }
  );
}

async function connectDB() {
  const connection = await mongoose.connect(process.env.MONGO_URI);
  await migrateAttendanceIndexes();
  console.log(`MongoDB Connected: ${connection.connection.host}`);
}

async function disconnectDB() {
  await mongoose.disconnect();
}

module.exports = { connectDB, disconnectDB, migrateAttendanceIndexes };
