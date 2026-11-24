'use strict';

function createSpriteStateMachine(spriteMeta) {
  const meta = spriteMeta || {};
  let slots = {};

  function resolveSpriteVisual(sp) {
    const entry = meta[sp.asset];
    if (!entry) {
      return {
        cid: String(sp.cid),
        kind: sp.kind || 'st',
        asset: sp.asset,
        baseSrc: sp.base ? `/common/sprites/${sp.base}.png` : '',
        faceSrc: '',
        fx: 0,
        fy: 0,
        fw: 0,
        fh: 0,
        fullReplace: false,
        x: sp.x,
        y: sp.y,
        w: sp.w || 155,
        h: sp.h || 296,
      };
    }
    const [baseKey, faceFile, fx, fy, fw, fh, fullFlag, metaW, metaH] = entry;
    return {
      cid: String(sp.cid),
      kind: sp.kind || (sp.asset.startsWith('up-') ? 'up' : 'st'),
      asset: sp.asset,
      baseSrc: fullFlag ? '' : `/common/sprites/${baseKey}.png`,
      faceSrc: faceFile ? `/common/faces/${faceFile}` : '',
      fx: fx || 0,
      fy: fy || 0,
      fw: fw || 0,
      fh: fh || 0,
      fullReplace: !!fullFlag,
      x: sp.x,
      y: sp.y,
      w: sp.w || metaW || 155,
      h: sp.h || metaH || 296,
    };
  }

  // Idempotent apply keyed strictly by character slot `cid` (NOT filename)
  function applySnapshot(snapshotMap) {
    const next = {};
    if (snapshotMap) {
      for (const cid of Object.keys(snapshotMap)) {
        const sp = snapshotMap[cid];
        if (!sp || !sp.asset) continue;
        const slotKey = String(sp.cid !== undefined ? sp.cid : cid);
        next[slotKey] = resolveSpriteVisual(Object.assign({}, sp, { cid: slotKey }));
      }
    }
    slots = next;
    return getInstances();
  }

  function applyCommand(cmd) {
    if (!cmd || !cmd.type) return getInstances();
    if (cmd.type === 'clearAll') {
      slots = {};
    } else if (cmd.type === 'remove') {
      delete slots[String(cmd.cid)];
    } else if (cmd.type === 'set') {
      const slotKey = String(cmd.cid);
      slots[slotKey] = resolveSpriteVisual(Object.assign({}, cmd, { cid: slotKey }));
    }
    return getInstances();
  }

  function getInstances() {
    const keys = Object.keys(slots).sort((a, b) => Number(a) - Number(b));
    return keys.map((k) => slots[k]);
  }

  function getSlotCount(cid) {
    return slots[String(cid)] ? 1 : 0;
  }

  return {
    applySnapshot,
    applyCommand,
    getInstances,
    getSlotCount,
    resolveSpriteVisual,
  };
}

module.exports = {
  createSpriteStateMachine,
};
