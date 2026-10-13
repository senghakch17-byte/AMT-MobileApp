function authorize(role) {
  return (req, res, next) => {
    if (!req.user || req.user.role !== role) {
      return res.status(403).json({ message: `Access Forbidden: Requires '${role}' permissions` });
    }
    next();
  };
}

module.exports = authorize;
