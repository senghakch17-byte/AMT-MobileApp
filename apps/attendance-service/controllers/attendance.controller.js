const mongoose = require('mongoose');

const Attendance = require('../models/attendance.model');
const { AppError } = require('../middleware/error.middleware');
const { parseDateOnly, utcDayStart } = require('../utils/date');

const STATUSES = Attendance.schema.path('status').enumValues;

function dateRange(query) {
  const range = {};
  if (query.from) range.$gte = parseDateOnly(query.from, 'from');
  if (query.to) {
    const to = parseDateOnly(query.to, 'to');
    to.setUTCDate(to.getUTCDate() + 1);
    range.$lt = to;
  }
  return Object.keys(range).length ? range : undefined;
}

async function checkIn(req, res) {
  const now = new Date();
  const attendance = await Attendance.create({
    userID: req.user.id,
    userEmail: req.user.emailid,
    attendanceDate: utcDayStart(now),
    checkIn: now,
    status: 'present',
  });
  res.status(201).json(attendance);
}

async function checkOut(req, res) {
  const filter = { userID: req.user.id, attendanceDate: utcDayStart(new Date()) };
  const attendance = await Attendance.findOneAndUpdate(
    { ...filter, checkOut: null },
    { $set: { checkOut: new Date() } },
    { new: true, runValidators: true }
  );

  if (attendance) return res.json(attendance);

  const existing = await Attendance.exists(filter);
  throw new AppError(existing ? 409 : 404, existing ? 'Already checked out today' : 'No check-in found for today');
}

async function listMine(req, res) {
  const filter = { userID: req.user.id };
  const range = dateRange(req.query);
  if (range) filter.attendanceDate = range;

  const records = await Attendance.find(filter).sort({ attendanceDate: -1 }).limit(100);
  res.json(records);
}

async function listAll(req, res) {
  const filter = {};
  if (req.query.userID) filter.userID = req.query.userID;
  const range = dateRange(req.query);
  if (range) filter.attendanceDate = range;

  const records = await Attendance.find(filter).sort({ attendanceDate: -1 }).limit(100);
  res.json(records);
}

function parseTimestamp(value, field) {
  if (value === null && field === 'checkOut') return null;
  if (typeof value !== 'string') throw new AppError(400, `${field} must be an ISO date-time string`);
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new AppError(400, `${field} must be a valid ISO date-time string`);
  return date;
}

async function updateAttendance(req, res) {
  if (!mongoose.isValidObjectId(req.params.id)) throw new AppError(400, 'Invalid attendance ID');

  const allowed = new Set(['attendanceDate', 'checkIn', 'checkOut', 'status']);
  const keys = Object.keys(req.body);
  if (!keys.length || keys.some((key) => !allowed.has(key))) {
    throw new AppError(400, 'Only attendanceDate, checkIn, checkOut, and status can be updated');
  }

  const attendance = await Attendance.findById(req.params.id);
  if (!attendance) throw new AppError(404, 'Attendance record not found');

  if ('attendanceDate' in req.body) attendance.attendanceDate = parseDateOnly(req.body.attendanceDate, 'attendanceDate');
  if ('checkIn' in req.body) attendance.checkIn = parseTimestamp(req.body.checkIn, 'checkIn');
  if ('checkOut' in req.body) attendance.checkOut = parseTimestamp(req.body.checkOut, 'checkOut');
  if ('status' in req.body) {
    if (!STATUSES.includes(req.body.status)) throw new AppError(400, `status must be one of: ${STATUSES.join(', ')}`);
    attendance.status = req.body.status;
  }
  if (attendance.checkIn && attendance.checkOut && attendance.checkOut < attendance.checkIn) {
    throw new AppError(400, 'checkOut cannot be before checkIn');
  }

  await attendance.save();
  res.json(attendance);
}

module.exports = { checkIn, checkOut, listMine, listAll, updateAttendance };
