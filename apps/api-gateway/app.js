const express = require('express');
const httpProxy = require('http-proxy');
const services = require('./config/services.config');
const authenticate = require('./middleware/authenticate.middleware');
const authorize = require('./middleware/authorize.middleware');
const rateLimit = require('./middleware/rateLimit.middleware');
const handleProxyError = require('./middleware/errorHandler.middleware');
const registerProxyRoutes = require('./routes/proxyRoutes');

const app = express();
const proxy = httpProxy.createProxyServer({
  proxyTimeout: 30000,
  timeout: 30000,
});

proxy.on('error', handleProxyError);

// DO NOT add express.json() here. http-proxy needs the unparsed raw request stream.
app.set('trust proxy', 1);
app.use(rateLimit({ windowMs: 60_000, max: 100 }));

registerProxyRoutes(app, proxy, services, {
  authenticate,
  authorize,
});

module.exports = app;
