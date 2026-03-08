const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy all API requests AND Auth0 specific routes
  app.use(
    ['/api', '/login', '/callback', '/logout'],
    createProxyMiddleware({
      target: 'http://127.0.0.1:5000',
      changeOrigin: true,
      pathFilter: function (path, req) {
        return path.match('^/api|^/login|^/callback|^/logout');
      },
      cookieDomainRewrite: 'localhost',
      onProxyRes: function (proxyRes, req, res) {
        var setCookie = proxyRes.headers['set-cookie'];
        if (setCookie) {
          proxyRes.headers['set-cookie'] = setCookie.map(cookie =>
            cookie.replace(/Secure;/i, '').replace(/SameSite=None/i, 'SameSite=Lax')
          );
        }
      }
    })
  );
};
