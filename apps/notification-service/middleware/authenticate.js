const jwt = require('jsonwebtoken');
const { jwtAlgorithm, jwtSecret } = require('../config');

function authenticate(req, res, next) {
  const [scheme, token] = (req.headers.authorization || '').split(' ');
  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ message: 'Access denied: token missing' });
  }

  try {
    req.user = jwt.verify(token, jwtSecret, { algorithms: [jwtAlgorithm] });
    if (!req.user.id || !req.user.role) {
      return res.status(401).json({ message: 'Invalid token claims' });
    }
    return next();
  } catch (_error) {
    return res.status(401).json({ message: 'Invalid or expired token' });
  }
}

module.exports = authenticate;
