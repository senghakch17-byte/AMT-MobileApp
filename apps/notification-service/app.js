const cors = require('cors');
const express = require('express');
const notificationsRouter = require('./routes/notifications');
const internalRouter = require('./routes/internal');
const preferencesRouter = require('./routes/preferences');
const { redisReady } = require('./services/eventConsumer');

const app = express();
app.use(cors());
app.use(express.json({ limit: '64kb' }));

app.get('/health', (_req, res) => {
  res.status(redisReady() ? 200 : 503).json({ status: redisReady() ? 'ok' : 'degraded', redis: redisReady() });
});
app.use('/api/v1/notifications', notificationsRouter);
app.use('/api/v1/notification-preferences', preferencesRouter);
app.use('/api/v1/internal', internalRouter);

app.use((error, _req, res, _next) => {
  console.error('[Notification] Request failed:', error);
  res.status(500).json({ message: 'Internal server error' });
});

module.exports = app;
