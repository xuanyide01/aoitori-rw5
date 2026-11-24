const fs = require('fs');
const path = require('path');

// Preserve pre-quantized PNG and JPEG asset bytes instead of letting image loaders re-encode them.
class PreserveWatchAssets {
  apply(compiler) {
    compiler.hooks.emit.tap({ name: 'PreserveWatchAssets', stage: 1000 }, () => {
      const source = path.join(__dirname, 'src/common');
      const dest = path.join(__dirname, 'build/common');
      function copy(dir) {
        for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
          const full = path.join(dir, item.name);
          if (item.isDirectory()) {
            copy(full);
          } else if (/\.(png|jpe?g)$/i.test(item.name)) {
            const target = path.join(dest, path.relative(source, full));
            fs.mkdirSync(path.dirname(target), { recursive: true });
            fs.copyFileSync(full, target);
          }
        }
      }
      copy(source);
    });
  }
}

module.exports = {
  postHook(config) {
    config.plugins.push(new PreserveWatchAssets());
  },
};
