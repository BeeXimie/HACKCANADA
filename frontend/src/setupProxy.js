const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  const hpmMiddleware = createProxyMiddleware({
    target: 'http://127.0.0.1:3000',
    changeOrigin: true,
    // By providing pathFilter here instead of as the first arg to app.use,
    // we ensure the paths are NOT stripped when forwarded to Flask.
    pathFilter: ['/api', '/login', '/callback', '/logout', '/onboarding', '/onboarding_confirm', '/profile', '/recommendations', '/scholarships', '/essay', '/applied'],
    cookieDomainRewrite: 'localhost',
    onProxyRes: function (proxyRes, req, res) {
      const setCookie = proxyRes.headers['set-cookie'];
      if (setCookie) {
        proxyRes.headers['set-cookie'] = setCookie.map(cookie =>
          cookie.replace(/Secure;/i, '').replace(/SameSite=None/i, 'SameSite=Lax')
        );
      }
    }
  });

  app.use(hpmMiddleware);
};
