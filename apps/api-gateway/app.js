const express = require('express');
const httpProxy = require('http-proxy');
const services = require('./config/services.config');
const authenticate = require('./middleware/authenticate.middleware');
const authorize = require('./middleware/authorize.middleware');
const rateLimit = require('./middleware/rateLimit.middleware');
const handleProxyError = require('./middleware/errorHandler.middleware');
const registerProxyRoutes = require('./routes/proxyRoutes');

const app = express();

// Proxy server configuration with a timeout of 30 seconds for both the proxy and the request. This ensures that requests to backend services do not hang indefinitely and provides a better user experience by returning an error if the backend service is unresponsive.
const proxy = httpProxy.createProxyServer({
  proxyTimeout: 30000,
  timeout: 30000,
});

// Handle errors that occur during proxying requests to backend services. This middleware captures any errors thrown by the proxy and sends an appropriate response to the client, ensuring that the API Gateway remains stable and provides meaningful error messages.
proxy.on('error', handleProxyError);

// Set the 'trust proxy' setting to 1 to ensure that the application correctly identifies the client's IP address when behind a reverse proxy or load balancer. This is important for accurate rate limiting and logging of client requests.
app.set('trust proxy', 1);

// Rate limiting middleware is applied globally to all routes. It uses Redis if REDIS_URL is set, otherwise it falls back to in-memory rate limiting for local development.
// The rate limit is set to 100 requests per minute per IP address. If the limit is exceeded, a 429 Too Many Requests response is returned.
app.use(rateLimit({ windowMs: 60_000, max: 100 }));

// Register proxy routes for each service defined in the configuration. Each route is protected by authentication and authorization middleware if specified in the service configuration. The proxy routes forward requests to the appropriate backend services based on the prefix defined in the configuration.
registerProxyRoutes(app, proxy, services, {
  authenticate,
  authorize,
});

module.exports = app;
