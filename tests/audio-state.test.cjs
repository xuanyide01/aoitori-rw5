'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createTitleMusicController, SCREEN_STATES } = require('../src/common/title-music.js');

function createMockAudio() {
  const events = [];
  return {
    events,
    play(src, loop) {
      events.push({ type: 'play', src, loop });
    },
    stop() {
      events.push({ type: 'stop' });
    },
    fadeOut(ms) {
      events.push({ type: 'fadeOut', ms });
    },
  };
}

test('TITLE <-> TITLE_SUB co-shares title BGM without restarting or stacking', () => {
  const adapter = createMockAudio();
  const ctrl = createTitleMusicController(adapter);

  const s1 = ctrl.transition(SCREEN_STATES.TITLE, { trueUnlocked: false, bgmEnabled: true });
  assert.equal(s1.screenState, 'TITLE');
  assert.equal(s1.currentTrack, '/common/title-bgm.opus');
  assert.equal(s1.isPlaying, true);
  assert.equal(s1.playStartCount, 1);

  // Enter Settings / Slots / Extra (TITLE_SUB)
  const s2 = ctrl.transition(SCREEN_STATES.TITLE_SUB);
  assert.equal(s2.screenState, 'TITLE_SUB');
  assert.equal(s2.currentTrack, '/common/title-bgm.opus');
  assert.equal(s2.playStartCount, 1);

  // Return to TITLE
  const s3 = ctrl.transition(SCREEN_STATES.TITLE);
  assert.equal(s3.screenState, 'TITLE');
  assert.equal(s3.playStartCount, 1);
  assert.equal(adapter.events.filter((e) => e.type === 'play').length, 1);
});

test('GAME state clears track completely and stops BGM including in-game menu', () => {
  const adapter = createMockAudio();
  const ctrl = createTitleMusicController(adapter);

  ctrl.transition(SCREEN_STATES.TITLE, { trueUnlocked: false, bgmEnabled: true });
  const gameSnap = ctrl.transition(SCREEN_STATES.GAME);
  assert.equal(gameSnap.screenState, 'GAME');
  assert.equal(gameSnap.currentTrack, '');
  assert.equal(gameSnap.isPlaying, false);

  // Simulated in-game pause/menu/settings stays in GAME and keeps track empty
  const stillGame = ctrl.transition(SCREEN_STATES.GAME, { immediate: true });
  assert.equal(stillGame.currentTrack, '');
  assert.equal(stillGame.isPlaying, false);

  // Returning to TITLE restarts playback
  const backTitle = ctrl.transition(SCREEN_STATES.TITLE, { trueUnlocked: true });
  assert.equal(backTitle.screenState, 'TITLE');
  assert.equal(backTitle.currentTrack, '/common/title-true-bgm.opus');
  assert.equal(backTitle.isPlaying, true);
  assert.equal(backTitle.playStartCount, 2);
});

test('Music room keeps identical title track uninterrupted on return, switches back otherwise', () => {
  const adapter = createMockAudio();
  const ctrl = createTitleMusicController(adapter);

  ctrl.transition(SCREEN_STATES.TITLE, { trueUnlocked: false, bgmEnabled: true });
  ctrl.transition(SCREEN_STATES.TITLE_SUB);
  const eventsBefore = adapter.events.length;

  // Case 1: Music room plays same title track -> return to TITLE_SUB must NOT stop or restart audio
  ctrl.adoptExternalTrack('/common/title-bgm.opus');
  const sameBack = ctrl.transition(SCREEN_STATES.TITLE_SUB, { trueUnlocked: false, bgmEnabled: true });
  assert.equal(sameBack.currentTrack, '/common/title-bgm.opus');
  assert.equal(sameBack.isPlaying, true);
  assert.equal(adapter.events.length, eventsBefore);

  // Case 2: Music room plays OP track -> return to TITLE_SUB must stop OP and switch back to title track
  ctrl.adoptExternalTrack('/common/opening-bgm.opus');
  const diffBack = ctrl.transition(SCREEN_STATES.TITLE_SUB, { trueUnlocked: false, bgmEnabled: true });
  assert.equal(diffBack.currentTrack, '/common/title-bgm.opus');
  assert.equal(diffBack.isPlaying, true);
  assert.equal(adapter.events[adapter.events.length - 2].type, 'stop');
  assert.equal(adapter.events[adapter.events.length - 1].src, '/common/title-bgm.opus');

  // Case 3: Music room plays a track while bgmEnabled=false -> return to TITLE_SUB stops it cleanly
  ctrl.adoptExternalTrack('/common/title-true-bgm.opus');
  const mutedBack = ctrl.transition(SCREEN_STATES.TITLE_SUB, { trueUnlocked: false, bgmEnabled: false });
  assert.equal(mutedBack.currentTrack, '');
  assert.equal(mutedBack.isPlaying, false);
  assert.equal(adapter.events[adapter.events.length - 1].type, 'stop');
});

test('Switching title background CG in settings syncs BGM track immediately', () => {
  const adapter = createMockAudio();
  const ctrl = createTitleMusicController(adapter);

  ctrl.transition(SCREEN_STATES.TITLE, { trueUnlocked: true, bgmEnabled: true, titleBgm: '/common/title-true-bgm.opus' });
  const sub = ctrl.transition(SCREEN_STATES.TITLE_SUB, { trueUnlocked: true, bgmEnabled: true, titleBgm: '/common/title-true-bgm.opus' });
  assert.equal(sub.currentTrack, '/common/title-true-bgm.opus');

  // Switch title CG preference to title01 -> music switches cleanly to title-bgm.opus
  const sw = ctrl.transition(SCREEN_STATES.TITLE_SUB, { trueUnlocked: true, bgmEnabled: true, titleBgm: '/common/title-bgm.opus' });
  assert.equal(sw.currentTrack, '/common/title-bgm.opus');
  assert.equal(sw.isPlaying, true);
  assert.equal(adapter.events[adapter.events.length - 2].type, 'stop');
  assert.equal(adapter.events[adapter.events.length - 1].src, '/common/title-bgm.opus');
});
