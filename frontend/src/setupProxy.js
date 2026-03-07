const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy all API requests AND Auth0 specific routes
  app.use(
    ['/api', '/login', '/callback', '/logout'],
    createProxyMiddleware({
      target: 'http://127.0.0.1:5000',
      changeOrigin: true,
    })
  );
};
