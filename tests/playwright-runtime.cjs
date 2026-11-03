const path = require('node:path');
module.exports = require(process.env.PLAYWRIGHT_MODULE || require.resolve('playwright', {
  paths: [path.resolve(__dirname, '../frontend')],
}));
