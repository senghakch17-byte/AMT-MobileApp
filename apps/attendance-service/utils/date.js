const { AppError } = require('../middleware/error.middleware');

function attendanceDay(date, timeZone = process.env.ATTENDANCE_TIME_ZONE || 'Asia/Phnom_Penh') {
  let parts;
  try {
    parts = new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(date);
  } catch {
    throw new AppError(500, 'ATTENDANCE_TIME_ZONE must be a valid IANA time zone');
  }
  const values = Object.fromEntries(parts.filter(({ type }) => type !== 'literal').map(({ type, value }) => [type, value]));
  return new Date(Date.UTC(Number(values.year), Number(values.month) - 1, Number(values.day)));
}

function parseDateOnly(value, field) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new AppError(400, `${field} must be a valid YYYY-MM-DD date`);
  }
  const date = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new AppError(400, `${field} must be a valid YYYY-MM-DD date`);
  }
  return date;
}

module.exports = { attendanceDay, parseDateOnly };
