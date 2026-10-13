const services = {
  register: process.env.REGISTER_SERVICE_URL,
  login: process.env.LOGIN_SERVICE_URL,
  request: process.env.REQUEST_SERVICE_URL,
  event: process.env.EVENT_SERVICE_URL,
};

console.log('[Gateway] Targets:', services);

if (!services.register || !services.login || !services.request || !services.event) {
  console.error('[Gateway] Missing one or more service URL env vars');
}

module.exports = services;
