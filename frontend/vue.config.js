const webpack = require('webpack')
const Dotenv = require('dotenv-webpack')

process.env.VUE_APP_VERSION = require('./package.json').version

module.exports = {
  filenameHashing: true,
  configureWebpack: {
    plugins: [
      new Dotenv(),
    ]
  },
}
