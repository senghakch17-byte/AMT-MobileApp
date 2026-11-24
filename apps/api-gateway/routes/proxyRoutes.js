function registerProxyRoutes(app, proxy, services, middleware) {
  const { authenticate } = middleware;
  const target = (service) => process.env[service.env];

  app.get('/health', (req, res) => {
    res.set('X-Gateway-Instance', process.env.HOSTNAME || 'local');
    res.json({ status: 'ok', instance: process.env.HOSTNAME || 'local' });
  });

  app.use(`/${services.register.prefix}`, (req, res) => {
    console.log('[Gateway] Routing to register Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.register) });
  });

  app.use(`/${services.login.prefix}`, (req, res) => {
    console.log('[Gateway] Routing to login Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.login) });
  });

  app.use(`/${services.request.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to request Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.request) });
  });

  app.use(`/${services.announcement.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to announcement Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.announcement) });
  });

  app.use(`/${services.attendance.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to attendance Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.attendance) });
  });

  app.use(`/${services.notification.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to notification Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.notification) });
  });

  app.use(`/${services.user.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to user Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.user) });
  });

  app.use(`/${services.booking.prefix}`, (req, res, next) => (
    req.path === '/health' ? next() : authenticate(req, res, next)
  ), (req, res) => {
    console.log('[Gateway] Routing to booking Service:', req.method, req.originalUrl);
    proxy.web(req, res, { target: target(services.booking) });
  });
}

module.exports = registerProxyRoutes;
