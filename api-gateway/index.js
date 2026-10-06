const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const httpProxy = require('http-proxy');
const jwt = require('jsonwebtoken');

const app = express();
const proxy = httpProxy.createProxyServer({
  proxyTimeout: 30000,
  timeout: 30000,
});

// DO NOT add express.json() here. http-proxy needs the unparsed raw request stream.

const JWT_SECRET = process.env.JWT_SECRET;

const REGISTER_SERVICE = process.env.REGISTER_SERVICE_URL;
const LOGIN_SERVICE = process.env.LOGIN_SERVICE_URL;
const FASTAPI_SERVICE = process.env.FASTAPI_SERVICE_URL;

console.log('[Gateway] Targets:', { REGISTER_SERVICE, LOGIN_SERVICE, FASTAPI_SERVICE });

if (!REGISTER_SERVICE || !LOGIN_SERVICE || !FASTAPI_SERVICE) {
  console.error('[Gateway] Missing one or more service URL env vars');
}

// Handle proxy errors gracefully
proxy.on('error', (err, req, res) => {
  console.error('Proxy Error:', err.code, err.message, '->', req.originalUrl);
  if (res && !res.headersSent) {
    res.status(502).json({
      message: 'Bad Gateway: Microservice unreachable',
      code: err.code,
    });
  }
});

// Middleware: Authenticate JWT Token
function authToken(req, res, next) {
  const header = req.headers.authorization;
  const token = header && header.split(' ')[1];

  if (!token) {
    return res.status(401).json({ message: 'Access Denied: Token missing' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(401).json({ message: 'Invalid or expired token', error: err.message });
    }
    req.user = user;
    next();
  });
}

// Middleware: Authorize Role
function authRole(role) {
  return (req, res, next) => {
    if (!req.user || req.user.role !== role) {
      return res.status(403).json({ message: `Access Forbidden: Requires '${role}' permissions` });
    }
    next();
  };
}

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// 1. REGISTER (public): /register/userregister -> register:5001/userregister
app.use('/register', (req, res) => {
  console.log('[Gateway] Routing to Register Service:', req.method, req.originalUrl);
  proxy.web(req, res, { target: REGISTER_SERVICE });
});

// 2. AUTH (public): /auth/login -> login:5002/login
app.use('/auth', (req, res) => {
  console.log('[Gateway] Routing to Authentication Service:', req.method, req.originalUrl);
  proxy.web(req, res, { target: LOGIN_SERVICE });
});

// 3. FASTAPI: /fastapi/... -> fastapi:8000/...
// To protect it, use: app.use('/fastapi', authToken, (req, res) => {...})
app.use('/fastapi', (req, res) => {
  console.log('[Gateway] Routing to FastAPI Service:', req.method, req.originalUrl);
  proxy.web(req, res, { target: FASTAPI_SERVICE });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`API Gateway Service is running on PORT NO : ${PORT}`);
});