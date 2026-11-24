'use strict';

function parseChunkText(text) {
  const lines = [];
  if (!text) return lines;
  const rawLines = String(text).split(/\r?\n/);
  let curBg = 'black';
  const curSprites = {};

  for (let i = 0; i < rawLines.length; i++) {
    const raw = rawLines[i];
    if (!raw) continue;
    if (raw.charCodeAt(0) === 64) { // '@'
      const parts = raw.split('\t');
      const cmd = parts[0];
      if (cmd === '@bg') {
        curBg = parts[1] || 'black';
      } else if (cmd === '@sp0') {
        for (const k of Object.keys(curSprites)) delete curSprites[k];
      } else if (cmd === '@sp-') {
        const cid = parts[1];
        if (cid !== undefined) delete curSprites[cid];
      } else if (cmd === '@sp' && parts.length >= 8) {
        const cid = String(parts[1]);
        curSprites[cid] = {
          cid,
          kind: parts[2],
          asset: parts[3],
          x: Number(parts[4]) || 0,
          y: Number(parts[5]) || 0,
          w: Number(parts[6]) || 176,
          h: Number(parts[7]) || 398,
        };
      }
      continue;
    }
    const tabIdx = raw.indexOf('\t');
    const speaker = tabIdx >= 0 ? raw.slice(0, tabIdx) : '';
    const body = tabIdx >= 0 ? raw.slice(tabIdx + 1) : raw;
    const snapSprites = {};
    for (const k of Object.keys(curSprites)) {
      snapSprites[k] = Object.assign({}, curSprites[k]);
    }
    lines.push({
      bg: curBg,
      sprites: snapSprites,
      speaker,
      text: body,
    });
  }
  return lines;
}

module.exports = { parseChunkText };
