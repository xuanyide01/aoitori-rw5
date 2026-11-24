'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const graph = require('../src/common/graph.js');
const gallery = require('../src/common/gallery.js');
const { createStoryEngine } = require('../src/common/engine.js');

test('graph and gallery metadata integrity', () => {
  assert.equal(graph.nodes.length, 100);
  assert.equal(graph.adultNodesCount, 28);
  assert.equal(graph.totalLines, 46987);
  assert.equal(graph.totalChunks, 184);
  assert.equal(graph.hSceneIds.length, 9);
  assert.equal(gallery.length, 117);
});

test('R18-only full progression follows complete main + H flow without script switching', () => {
  const engine = createStoryEngine(graph);

  const nextAfterSn101 = engine.resolveNextNode('sn101');
  assert.equal(nextAfterSn101.id, 'sn101_h1');
  assert.equal(nextAfterSn101.adult, true);

  const nextAfterH1 = engine.resolveNextNode('sn101_h1');
  assert.equal(nextAfterH1.id, 'sn101_p2');

  assert.equal(engine.listVisibleChapters().length, 100);
  assert.equal(engine.listHScenes().length, 9);
  assert.equal(engine.filterGallery(gallery).length, 117);
});

test('route choices sn108 and sn603 match expected targets', () => {
  const engine = createStoryEngine(graph);
  const sn108 = engine.getNode('sn108');
  assert.equal(sn108.choices.length, 3);
  assert.deepEqual(
    sn108.choices.map((c) => c.next),
    ['sn201', 'sn301', 'sn401']
  );
  const sn603 = engine.getNode('sn603');
  assert.equal(sn603.choices.length, 1);
  assert.equal(sn603.choices[0].label, '『喜欢这个世界』');
  assert.equal(engine.resolveChoiceTarget(sn603.choices[0].next).id, 'sn604');
});

test('unlocks progress state machine aligns title states V12=0/1/2 and buttons with menu.ps3', () => {
  const engine = createStoryEngine(graph);
  let p = engine.normalizeProgress(null);
  const t0 = engine.getTitlePresentation(p);
  assert.equal(t0.stateId, 0);
  assert.equal(t0.showAkariRoute, false);
  assert.deepEqual(t0.buttons, ['start', 'load', 'extra', 'config', 'exit']);

  p = engine.applyNodeUnlocks(p, engine.getNode('sn103'));
  assert.equal(p.title02, true);
  const t1 = engine.getTitlePresentation(p);
  assert.equal(t1.stateId, 1);
  assert.equal(t1.showAkariRoute, false);
  assert.deepEqual(t1.buttons, ['start', 'load', 'extra', 'config', 'exit']);

  p = engine.applyNodeUnlocks(p, engine.getNode('sn299'));
  p = engine.applyNodeUnlocks(p, engine.getNode('sn399'));
  assert.equal(p.trueUnlocked, false);
  p = engine.applyNodeUnlocks(p, engine.getNode('sn499'));
  assert.equal(p.trueUnlocked, true);
  const t2 = engine.getTitlePresentation(p);
  assert.equal(t2.stateId, 2);
  assert.equal(t2.showAkariRoute, true);
  assert.deepEqual(t2.buttons, ['start', 'akari', 'load', 'extra', 'config', 'exit']);
});
