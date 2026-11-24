'use strict';

function createDefaultProgress() {
  return {
    title02: false,     // set at sn103 -> P[2147]=1
    clearRisa: false,   // set at sn299 -> P[2150]=1
    clearSayo: false,   // set at sn399 -> P[2151]=1
    clearMari: false,   // set at sn499 -> P[2152]=1
    clearTrue: false,   // set at sn605 -> P[2153]=1
    trueUnlocked: false // P[2156]=1 when clearRisa && clearSayo && clearMari
  };
}

function normalizeProgress(raw) {
  const p = Object.assign(createDefaultProgress(), raw || {});
  if (p.clearRisa && p.clearSayo && p.clearMari) {
    p.trueUnlocked = true;
  }
  return p;
}

// Mirrors menu.ps3 V12=0/1/2 progression, with optional user selection across unlocked title CGs:
// - V12=0: title01 + bgm36 + 5 buttons (开始游戏, 继续游戏, 鉴赏模式, 系统设定, 结束游戏)
// - V12=1: title02 + bgm36 + 5 buttons (unlocked at sn103 P[2147]=1)
// - V12=2: title03 + bgm33 + 6 buttons (adds 明里篇 at index 1 after 开始游戏; unlocked at P[2156]=1)
function getTitlePresentation(progress, preferredTitleId) {
  const p = normalizeProgress(progress);
  const unlockedTitles = ['title01'];
  if (p.title02) unlockedTitles.push('title02');
  if (p.trueUnlocked) unlockedTitles.push('title03');

  const autoId = p.trueUnlocked ? 'title03' : (p.title02 ? 'title02' : 'title01');
  const activeTitleId = (preferredTitleId && unlockedTitles.indexOf(preferredTitleId) >= 0)
    ? preferredTitleId
    : autoId;

  const stateId = activeTitleId === 'title03' ? 2 : (activeTitleId === 'title02' ? 1 : 0);
  const bg = '/common/images/' + activeTitleId + '.jpg';
  const bgm = activeTitleId === 'title03' ? '/common/title-true-bgm.opus' : '/common/title-bgm.opus';
  const buttons = p.trueUnlocked
    ? ['start', 'akari', 'load', 'extra', 'config', 'exit']
    : ['start', 'load', 'extra', 'config', 'exit'];

  return {
    stateId,
    activeTitleId,
    unlockedTitles,
    bg,
    bgm,
    showAkariRoute: !!p.trueUnlocked,
    showTrueRoute: !!p.trueUnlocked,
    buttons,
  };
}

function applyNodeUnlocks(progress, node) {
  const next = normalizeProgress(progress);
  if (!node || !Array.isArray(node.unlocks)) return next;
  for (let i = 0; i < node.unlocks.length; i++) {
    const tag = node.unlocks[i];
    if (tag === 'title02') next.title02 = true;
    else if (tag === 'clear_risa') next.clearRisa = true;
    else if (tag === 'clear_sayo') next.clearSayo = true;
    else if (tag === 'clear_mari') next.clearMari = true;
    else if (tag === 'clear_true') next.clearTrue = true;
  }
  if (next.clearRisa && next.clearSayo && next.clearMari) {
    next.trueUnlocked = true;
  }
  return next;
}

function createStoryEngine(graph) {
  const nodes = (graph && graph.nodes) || [];
  const nodeMap = {};
  for (let i = 0; i < nodes.length; i++) {
    nodeMap[nodes[i].id] = nodes[i];
  }

  function getNode(id) {
    return nodeMap[id] || null;
  }

  function resolveStartNode(requestedId) {
    return getNode(requestedId || (graph && graph.startNode) || 'sn101');
  }

  function resolveNextNode(nodeId) {
    const node = getNode(nodeId);
    if (!node || !node.next) return null;
    return getNode(node.next);
  }

  function resolveChoiceTarget(choiceNextId) {
    return getNode(choiceNextId);
  }

  function listVisibleChapters(routeFilter) {
    if (!routeFilter || routeFilter === 'all') return nodes.slice();
    return nodes.filter((n) => n.route === routeFilter);
  }

  function filterGallery(galleryGroups) {
    return Array.isArray(galleryGroups) ? galleryGroups.slice() : [];
  }

  function listHScenes() {
    return nodes.filter((n) => n.route === 'hscene');
  }

  return {
    getNode,
    resolveStartNode,
    resolveNextNode,
    resolveChoiceTarget,
    listVisibleChapters,
    filterGallery,
    listHScenes,
    getTitlePresentation,
    applyNodeUnlocks,
    normalizeProgress,
  };
}

module.exports = {
  createDefaultProgress,
  normalizeProgress,
  getTitlePresentation,
  applyNodeUnlocks,
  createStoryEngine,
};
