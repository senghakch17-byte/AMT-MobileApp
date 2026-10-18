const isAdminRoute = {
  attendance: (req) => (req.method === 'GET' && req.path === '/') || req.method === 'PATCH',
  event: (req) => ['POST', 'PATCH', 'DELETE'].includes(req.method),
  library: (req) => {
    const path = req.path;
    return (path === '/api/v1/rooms' && req.method === 'POST')
      || (/^\/api\/v1\/rooms\/[^/]+$/.test(path) && ['PATCH', 'DELETE'].includes(req.method))
      || (path === '/api/v1/books' && req.method === 'POST')
      || (/^\/api\/v1\/books\/[^/]+$/.test(path) && ['PATCH', 'DELETE'].includes(req.method))
      || (path === '/api/v1/bookings' && req.method === 'GET')
      || (/^\/api\/v1\/bookings\/[^/]+\/(approve|reject)$/.test(path) && req.method === 'POST');
  },
};

// Default gateway routes keep existing behavior when GATEWAY_SERVICES is not set.
const DEFAULT_SERVICE_ROUTES = [
  { prefix: 'register', env: 'REGISTER_SERVICE_URL', protected: false },
  { prefix: 'auth', env: 'LOGIN_SERVICE_URL', protected: false },
  { prefix: 'request', env: 'REQUEST_SERVICE_URL', protected: true },
  { prefix: 'event', env: 'EVENT_SERVICE_URL', protected: true, adminRoute: isAdminRoute.event },
  { prefix: 'attendance', env: 'ATTENDANCE_SERVICE_URL', protected: true, adminRoute: isAdminRoute.attendance },
  { prefix: 'notification', env: 'NOTIFICATION_SERVICE_URL', protected: true },
  { prefix: 'members', env: 'MEMBER_SERVICE_URL', protected: true },
  { prefix: 'member', env: 'MEMBER_SERVICE_URL', protected: true },
  { prefix: 'library', env: 'LIBRARY_SERVICE_URL', protected: true, adminRoute: isAdminRoute.library },
];

// Resolve each service target from its environment variable name.
// services = [ { prefix: 'register', env: 'REGISTER_SERVICE_URL', protected: false, target: process.env.REGISTER_SERVICE_URL }, ... ]
const services = DEFAULT_SERVICE_ROUTES.map((service) => ({
  ...service,
  target: process.env[service.env],
}));

// Log active targets once on startup to make gateway routing easy to inspect.
console.log('[Gateway] Targets:', services.reduce((targets, service) => ({
  ...targets,
  [service.prefix]: service.target,
}), {}));

// Detect incomplete config early instead of failing later during proxy calls.
const missingServices = services.filter((service) => !service.prefix || !service.env || !service.target);

if (missingServices.length) {
  console.error('[Gateway] Missing service route config:', missingServices);
}

module.exports = services;
