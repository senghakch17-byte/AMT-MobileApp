const jwt = require('jsonwebtoken');

function authenticate(req, res, next) {
  const match = /^Bearer (\S+)$/i.exec(req.headers.authorization || '');
  if (!match) return res.status(401).json({ message: 'Access Denied: Token missing' });

  try {
    const user = jwt.verify(match[1], process.env.JWT_SECRET, { algorithms: ['HS256'] });
    if (!user.id || !user.emailid || !user.role) {
      return res.status(401).json({ message: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  } catch {
    res.status(401).json({ message: 'Invalid or expired token' });
  }
}

function requireAdmin(req, res, next) {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: "Access Forbidden: Requires 'admin' permissions" });
  }
  next();
}

module.exports = { authenticate, requireAdmin };
