// const webpack = require('webpack')

const fs = require('fs')
const packageJson = fs.readFileSync('./package.json')
const version = JSON.parse(packageJson).version || 0

process.env.VUE_APP_VERSION = version

module.exports = {
  filenameHashing: true,
  devServer: {
    proxy: 'http://localhost:5000'
  }
}
