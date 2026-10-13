function rateLimit({ windowMs = 60_000, max = 100 } = {}) {
  const hits = new Map();

  return (req, res, next) => {
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

module.exports = rateLimit;
