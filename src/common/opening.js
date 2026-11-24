'use strict';

function pad4(n) {
  const s = String(Math.max(0, Math.floor(n)));
  if (s.length >= 4) return s;
  return ('0000' + s).slice(-4);
}

function getOpeningFrameUri(index) {
  return '/common/opening/f' + pad4(index) + '.jpg';
}

function getOpeningFrameIndexAtMs(elapsedMs, meta) {
  const count = (meta && meta.frameCount) || 583;
  const dur = (meta && meta.durationMs) || 121458;
  if (elapsedMs <= 0) return 0;
  const ratio = Math.min(0.99999, Math.max(0, elapsedMs / dur));
  return Math.min(count - 1, Math.floor(ratio * count));
}

module.exports = {
  getOpeningFrameUri,
  getOpeningFrameIndexAtMs,
};
