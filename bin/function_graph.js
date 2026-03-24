#!/usr/bin/env node
require('ts-node').register({
  transpileOnly: true,
  project: require('path').join(__dirname, '..', 'tsconfig.json'),
});
require('../src/index');
