const mongoose = require('mongoose');

const attendanceSchema = new mongoose.Schema(
  {
    userID: { type: String, required: true, trim: true, immutable: true },
    userEmail: { type: String, required: true, trim: true, lowercase: true, immutable: true },
    attendanceDate: { type: Date, required: true },
    checkIn: { type: Date, default: null },
    checkOut: { type: Date, default: null },
    status: {
      type: String,
      enum: ['present', 'late', 'absent', 'excused'],
      default: 'present',
      required: true,
    },
  },
  { timestamps: true }
);

attendanceSchema.index({ userID: 1, attendanceDate: 1 }, { unique: true });
attendanceSchema.index({ attendanceDate: -1, status: 1 });

module.exports = mongoose.model('Attendance', attendanceSchema);
