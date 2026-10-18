function registerProxyRoutes(app, proxy, services, middleware) {
  const { authenticate, authorize } = middleware;

  app.get('/health', (req, res) => res.json({ status: 'ok' }));

  services.forEach((service) => {
    const middlewareStack = service.protected || service.role ? [authenticate] : [];

    if (service.role) {
      middlewareStack.push(authorize(service.role));
    }

    if (service.adminRoute) {
      middlewareStack.push((req, res, next) => (service.adminRoute(req) ? authorize('admin')(req, res, next) : next()));
    }

    app.use(`/${service.prefix}`, ...middlewareStack, (req, res) => {
      console.log(`[Gateway] Routing to ${service.prefix} Service:`, req.method, req.originalUrl);
      proxy.web(req, res, { target: service.target });
    });
  });
}

module.exports = registerProxyRoutes;
