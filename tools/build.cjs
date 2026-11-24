'use strict';

const fs = require('fs');
const path = require('path');

const watchConfig = path.resolve('src/config-watch.json');
if (!fs.existsSync(watchConfig)) {
  throw new Error('src/config-watch.json is required');
}
JSON.parse(fs.readFileSync(watchConfig, 'utf8'));

const candidates = [
  process.env.WATCH_COMPAT_TOOLKIT,
  'D:/codex/移植项目/shinuyakata-rw5/源码/tools/compat-toolkit/node_modules/aiot-toolkit',
  'D:/DSH/baseline/node_modules/aiot-toolkit',
].filter(Boolean);

const toolkit = candidates.find((p) => fs.existsSync(path.join(p, 'package.json')));
if (!toolkit) {
  throw new Error('aiot-toolkit 1.1.0 not found');
}
const tkPkg = JSON.parse(fs.readFileSync(path.join(toolkit, 'package.json'), 'utf8'));
if (tkPkg.version !== '1.1.0') {
  throw new Error('Compatible compiler must be aiot-toolkit 1.1.0, got ' + tkPkg.version);
}

const { compile } = require(path.join(toolkit, 'lib/commands/compile'));

(async () => {
  const result = await compile('native', process.argv.includes('--development') ? 'dev' : 'prod', false, {
    signMode: 'BUILD',
  });
  if (result.compileError || (result.stats && result.stats.hasErrors())) {
    throw new Error('aiot-toolkit compile failed');
  }
  const manifest = JSON.parse(fs.readFileSync('src/manifest.json', 'utf8'));
  const name = manifest.package + '.debug.' + manifest.versionName + '.rpk';
  const rpkPath = path.join('dist', name);
  if (!fs.existsSync(rpkPath)) {
    throw new Error('Package was not produced: ' + rpkPath);
  }
  const packaging = await require('./repack-rpk.cjs').repackRpk(rpkPath, rpkPath, toolkit);
  const binPath = path.join('dist', manifest.package + '.' + manifest.versionName + '.bin');
  fs.copyFileSync(rpkPath, binPath);

  console.log('R1_PACKAGING', JSON.stringify(packaging));
  const bytes = fs.statSync(rpkPath).size;
  if (bytes >= 25000000) {
    throw new Error('Package exceeds 25,000,000-byte cap: ' + bytes);
  }
  console.log('BUILD_OUTPUT', name, bytes);
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
