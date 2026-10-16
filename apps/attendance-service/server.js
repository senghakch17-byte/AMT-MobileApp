const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const app = require('./app');
const { connectDB, disconnectDB } = require('./config/db');

const PORT = process.env.PORT || 8002;

async function start() {
  if (!process.env.MONGO_URI || !process.env.JWT_SECRET) {
    throw new Error('MONGO_URI and JWT_SECRET are required');
  }
  await connectDB();
  const server = app.listen(PORT, () => console.log(`Attendance Service running on port ${PORT}`));

  async function shutdown() {
    server.close(async () => {
      await disconnectDB();
      process.exit(0);
    });
  }
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

start().catch((error) => {
  console.error(`Attendance Service startup failed: ${error.message}`);
  process.exit(1);
});
