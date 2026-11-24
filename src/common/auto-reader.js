'use strict';

const AUTO_CHAR_INTERVAL_MS = 30;
const AUTO_BASE_DELAY_MS = {
  slow: 2600,
  normal: 1500,
  fast: 800,
};

function computeAutoDelayMs(text, speedLevel) {
  const len = text ? String(text).length : 0;
  const base = AUTO_BASE_DELAY_MS[speedLevel] || AUTO_BASE_DELAY_MS.normal;
  const extraChars = Math.max(0, len - 60);
  const extraMs = Math.min(5000, extraChars * 55);
  return base + extraMs;
}

function getTypewriterConfig(autoEnabled, manualTextSpeed) {
  if (autoEnabled) {
    return {
      enabled: true,
      charStep: 1,
      intervalMs: AUTO_CHAR_INTERVAL_MS,
    };
  }
  const speed = Number(manualTextSpeed) || 0;
  return {
    enabled: speed > 0,
    charStep: 2,
    intervalMs: speed,
  };
}

module.exports = {
  AUTO_CHAR_INTERVAL_MS,
  AUTO_BASE_DELAY_MS,
  computeAutoDelayMs,
  getTypewriterConfig,
};
