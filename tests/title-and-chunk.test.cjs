'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { getTitlePresentation } = require('../src/common/engine.js');
const { parseChunkText } = require('../src/common/chunk-codec.js');
const { getOpeningFrameUri, getOpeningFrameIndexAtMs } = require('../src/common/opening.js');
const { computeAutoDelayMs, getTypewriterConfig } = require('../src/common/auto-reader.js');
const openingMeta = require('../src/common/opening-meta.js');

test('title presentation matches menu.ps3 V12=0/1/2 progression table', () => {
  const s0 = getTitlePresentation({ title02: false, clearRisa: false, clearSayo: false, clearMari: false });
  assert.equal(s0.stateId, 0);
  assert.equal(s0.bg, '/common/images/title01.jpg');
  assert.equal(s0.bgm, '/common/title-bgm.opus');
  assert.equal(s0.showAkariRoute, false);

  const s1 = getTitlePresentation({ title02: true, clearRisa: false, clearSayo: false, clearMari: false });
  assert.equal(s1.stateId, 1);
  assert.equal(s1.bg, '/common/images/title02.jpg');
  assert.equal(s1.bgm, '/common/title-bgm.opus');
  assert.equal(s1.showAkariRoute, false);

  const s2 = getTitlePresentation({ title02: true, clearRisa: true, clearSayo: true, clearMari: true });
  assert.equal(s2.stateId, 2);
  assert.equal(s2.bg, '/common/images/title03.jpg');
  assert.equal(s2.bgm, '/common/title-true-bgm.opus');
  assert.equal(s2.showAkariRoute, true);
  assert.deepEqual(s2.unlockedTitles, ['title01', 'title02', 'title03']);

  // Switching background CG in settings syncs BGM while keeping unlocked 明里篇 accessible
  const sw1 = getTitlePresentation({ title02: true, clearRisa: true, clearSayo: true, clearMari: true }, 'title01');
  assert.equal(sw1.bg, '/common/images/title01.jpg');
  assert.equal(sw1.bgm, '/common/title-bgm.opus');
  assert.equal(sw1.showAkariRoute, true);

  // Locked title03 cannot be forced when not unlocked
  const locked = getTitlePresentation({ title02: true, clearRisa: false, clearSayo: false, clearMari: false }, 'title03');
  assert.equal(locked.bg, '/common/images/title02.jpg');
  assert.equal(locked.bgm, '/common/title-bgm.opus');
});

test('chunk codec parses actual generated chunks cleanly', () => {
  const sn101Path = path.resolve(__dirname, '../src/common/story/sn101.txt');
  const txt = fs.readFileSync(sn101Path, 'utf8');
  const lines = parseChunkText(txt);
  assert.ok(lines.length > 0);
  assert.ok(lines.every((l) => typeof l.bg === 'string' && typeof l.text === 'string' && typeof l.sprites === 'object'));
});

test('opening helpers and auto reader compute valid bounds', () => {
  assert.equal(getOpeningFrameUri(0), '/common/opening/f0000.jpg');
  assert.equal(getOpeningFrameUri(416), '/common/opening/f0416.jpg');
  assert.equal(getOpeningFrameIndexAtMs(0, openingMeta), 0);
  assert.equal(getOpeningFrameIndexAtMs(openingMeta.durationMs + 5000, openingMeta), openingMeta.frameCount - 1);

  assert.equal(computeAutoDelayMs('测试对白', 'slow'), 2600);
  assert.equal(computeAutoDelayMs('测试对白', 'normal'), 1500);
  assert.equal(computeAutoDelayMs('测试对白', 'fast'), 800);

  const exactly60 = '一'.repeat(60);
  const len61 = '一'.repeat(61);
  const len200 = '一'.repeat(200);
  assert.equal(computeAutoDelayMs(exactly60, 'normal'), 1500);
  assert.equal(computeAutoDelayMs(len61, 'normal'), 1555);
  assert.equal(computeAutoDelayMs(len200, 'slow'), 7600);
  assert.equal(computeAutoDelayMs(len200, 'normal'), 6500);
  assert.equal(computeAutoDelayMs(len200, 'fast'), 5800);

  assert.deepEqual(getTypewriterConfig(true, 0), { enabled: true, charStep: 1, intervalMs: 30 });
  assert.deepEqual(getTypewriterConfig(true, 28), { enabled: true, charStep: 1, intervalMs: 30 });
  assert.deepEqual(getTypewriterConfig(false, 0), { enabled: false, charStep: 2, intervalMs: 0 });
  assert.deepEqual(getTypewriterConfig(false, 28), { enabled: true, charStep: 2, intervalMs: 28 });
});
