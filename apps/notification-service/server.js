require('dotenv').config();

const app = require('./app');
const { port } = require('./config');
const { connectDatabase, disconnectDatabase } = require('./db');
const { startConsumer, stopConsumer } = require('./services/eventConsumer');

let server;

async function start() {
  await connectDatabase();
  await startConsumer();
  server = app.listen(port, () => console.log(`[Notification] Service listening on port ${port}`));
}

async function shutdown(signal) {
  console.log(`[Notification] Received ${signal}; shutting down`);
  server?.close();
  await stopConsumer();
  await disconnectDatabase();
  process.exit(0);
}

process.on('SIGTERM', () => void shutdown('SIGTERM'));
process.on('SIGINT', () => void shutdown('SIGINT'));

start().catch((error) => {
  console.error('[Notification] Startup failed:', error);
  process.exit(1);
});
