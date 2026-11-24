'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const spriteMeta = require('../src/common/sprite-meta.js');
const { createSpriteStateMachine } = require('../src/common/sprite-machine.js');

test('native aspect ratios preserved across st-, up-, and square phone inserts', () => {
  const mrStand = spriteMeta['st-mr_b102'];
  const ykStand = spriteMeta['st-yk_a504'];
  const tdPhone = spriteMeta['st-td_b199'];
  const rsUp = spriteMeta['up-rs_a101'];
  assert.ok(mrStand && ykStand && tdPhone && rsUp);
  // st-mr_b102 (122x296), st-yk_a504 (133x296), st-td_b199 (144x144), up-rs_a101 (253x256)
  assert.equal(mrStand[8], 296);
  assert.equal(ykStand[8], 296);
  assert.equal(tdPhone[7], 144);
  assert.equal(tdPhone[8], 144);
  assert.equal(rsUp[8], 256);
  assert.ok(rsUp[7] > 230 && mrStand[7] < 140);
});

test('idempotent slot-keyed sprite machine never stacks duplicates per cid', () => {
  const sm = createSpriteStateMachine(spriteMeta);

  let list = sm.applySnapshot({
    '0': { cid: '0', kind: 'st', asset: 'st-ak_a204', x: 134, y: 0, w: 165, h: 296 },
    '1': { cid: '1', kind: 'st', asset: 'st-mr_a402', x: 226, y: 0, w: 197, h: 296 },
  });
  assert.equal(list.length, 2);
  assert.equal(sm.getSlotCount('0'), 1);
  assert.equal(sm.getSlotCount('1'), 1);

  const swaps = ['st-ak_a421', 'up-ak_a912', 'up-ak_a421', 'st-ak_a812', 'st-ak_a204'];
  for (const asset of swaps) {
    const kind = asset.startsWith('up-') ? 'up' : 'st';
    const m = spriteMeta[asset];
    list = sm.applyCommand({
      type: 'set',
      cid: '0',
      kind,
      asset,
      x: 130,
      y: kind === 'up' ? -12 : 0,
      w: m[7],
      h: m[8],
    });
    assert.equal(sm.getSlotCount('0'), 1);
    assert.equal(list.length, 2);
    assert.equal(list.filter((i) => i.cid === '0').length, 1);
    assert.equal(list[0].asset, asset);
  }

  list = sm.applySnapshot({
    '0': { cid: '0', kind: 'st', asset: 'st-ak_a204', x: 134, y: 0, w: 165, h: 296 },
  });
  assert.equal(list.length, 1);
  assert.equal(sm.getSlotCount('0'), 1);
  assert.equal(sm.getSlotCount('1'), 0);

  list = sm.applyCommand({ type: 'clearAll' });
  assert.equal(list.length, 0);
});
