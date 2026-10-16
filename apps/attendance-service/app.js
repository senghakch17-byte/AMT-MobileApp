const express = require('express');

const attendanceRoutes = require('./routes/attendance.routes');
const { errorHandler, notFound } = require('./middleware/error.middleware');

const app = express();
app.use(express.json({ limit: '100kb' }));
app.use('/', attendanceRoutes);
app.use(notFound);
app.use(errorHandler);

module.exports = app;
