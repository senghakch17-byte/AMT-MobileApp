const { createClient } = require('redis');

function createMemoryRateLimit({ windowMs, max }) {
  const hits = new Map();

  return (req, res, next) => {
    // In-memory fallback keeps local development working when REDIS_URL is not set.
    const key = req.ip;
    const now = Date.now();
    const entry = hits.get(key);

    if (!entry || now - entry.startedAt > windowMs) {
      hits.set(key, { count: 1, startedAt: now });
      return next();
    }

    entry.count += 1;

    if (entry.count > max) {
      return res.status(429).json({ message: 'Too many requests' });
    }

    next();
  };
}

function rateLimit({ windowMs = 60_000, max = 100 } = {}) {
  const redisUrl = process.env.REDIS_URL;

  if (!redisUrl) {
    return createMemoryRateLimit({ windowMs, max });
  }

  const client = createClient({ url: redisUrl });
  const connectPromise = client.connect().catch((err) => {
    // Redis failures should not block the gateway; requests continue without counting.
    console.error('[Gateway] Redis rate limit unavailable:', err.message);
  });

  return async (req, res, next) => {
    const key = `rate-limit:${req.ip}`;

    try {
      // Wait for Redis connection once, then share rate counts across gateway containers.
      await connectPromise;

      if (!client.isReady) {
        return next();
      }

      const count = await client.incr(key);

      if (count === 1) {
        await client.pExpire(key, windowMs);
      }

      if (count > max) {
        return res.status(429).json({ message: 'Too many requests' });
      }

      next();
    } catch (err) {
      // Fail open so Redis outage does not cause API outage.
      console.error('[Gateway] Redis rate limit error:', err.message);
      next();
    }
  };
}

module.exports = rateLimit;
