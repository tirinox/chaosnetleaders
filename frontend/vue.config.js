const webpack = require('webpack')

module.exports = {
  filenameHashing: true,
  configureWebpack: config => {
    return {
      plugins: [
        new webpack.DefinePlugin({
          // eslint-disable-next-line no-undef
          'APPLICATION_VERSION': JSON.stringify(require('./package.json').version),
        })
      ]
    }
  },
}
