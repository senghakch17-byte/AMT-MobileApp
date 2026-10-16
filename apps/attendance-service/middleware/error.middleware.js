class AppError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function notFound(req, res) {
  res.status(404).json({ message: 'Route not found' });
}

function errorHandler(error, req, res, next) {
  if (res.headersSent) return next(error);
  if (error.code === 11000) {
    return res.status(409).json({ message: 'Attendance record already exists for this user and date' });
  }
  if (error.name === 'ValidationError' || error.name === 'CastError') {
    return res.status(400).json({ message: error.message });
  }
  const status = error.status || 500;
  if (status === 500) console.error(error);
  res.status(status).json({ message: status === 500 ? 'Server error' : error.message });
}

module.exports = { AppError, errorHandler, notFound };
