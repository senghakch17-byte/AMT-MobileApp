function registerProxyRoutes(app, proxy, targets, middleware) {
  const { register, login, request, event } = targets;
  const { authenticate } = middleware;

  app.get('/health', (req, res) => res.json({ status: 'ok' }));

  app.use('/register', (req, res) => {
    console.log('[Gateway] Routing to Register Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: register });
  });

  app.use('/auth', (req, res) => {
    console.log('[Gateway] Routing to Authentication Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: login });
  });

  app.use('/request', authenticate, (req, res) => {
    console.log('[Gateway] Routing to Request Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: request });
  });

  app.use('/event', authenticate, (req, res) => {
    console.log('[Gateway] Routing to Event Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: event });
  });
}

module.exports = registerProxyRoutes;
