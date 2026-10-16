function handleProxyError(err, req, res) {
  console.error('Proxy Error:', err.code, err.message, '->', req.originalUrl);
  if (res && !res.headersSent) {
    res.status(502).json({
      message: 'Bad Gateway: Microservice unreachable',
      code: err.code,
    });
  }
}

module.exports = handleProxyError;
