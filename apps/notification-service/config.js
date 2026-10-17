const required = ['MONGO_URI', 'JWT_SECRET'];

for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`${key} environment variable is required`);
  }
}

module.exports = {
  port: Number(process.env.PORT || 8005),
  mongoUri: process.env.MONGO_URI,
  jwtSecret: process.env.JWT_SECRET,
  jwtAlgorithm: process.env.JWT_ALGORITHM || 'HS256',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  redisStreamKey: process.env.REDIS_STREAM_KEY || 'notification:events',
  redisConsumerGroup: process.env.REDIS_CONSUMER_GROUP || 'notification-service',
  // A stable name lets a restarted single worker resume its pending deliveries.
  redisConsumerName: process.env.REDIS_CONSUMER_NAME || 'notification-worker',
  internalApiKey: process.env.INTERNAL_API_KEY,
};
