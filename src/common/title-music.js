'use strict';

const SCREEN_STATES = {
  TITLE: 'TITLE',
  TITLE_SUB: 'TITLE_SUB',
  GAME: 'GAME',
};

function createTitleMusicController(adapter) {
  // adapter: optional { play(src, loop), stop(), fadeOut(ms) }
  const audio = adapter || {
    play() {},
    stop() {},
    fadeOut() {},
  };

  let screenState = SCREEN_STATES.TITLE;
  let currentTrack = '';
  let isPlaying = false;
  let playStartCount = 0;
  let trueUnlocked = false;
  let bgmEnabled = true;
  let customTitleBgm = '';

  function desiredTrackForTitle() {
    if (!bgmEnabled) return '';
    if (customTitleBgm) return customTitleBgm;
    return trueUnlocked ? '/common/title-true-bgm.opus' : '/common/title-bgm.opus';
  }

  function transition(nextState, opts) {
    const options = opts || {};
    if (options.trueUnlocked !== undefined) trueUnlocked = !!options.trueUnlocked;
    if (options.bgmEnabled !== undefined) bgmEnabled = !!options.bgmEnabled;
    if (options.titleBgm !== undefined) customTitleBgm = options.titleBgm || '';

    if (!SCREEN_STATES[nextState]) {
      throw new Error('Invalid screenState: ' + nextState);
    }

    const prevState = screenState;
    screenState = nextState;

    if (nextState === SCREEN_STATES.GAME) {
      if (isPlaying || currentTrack) {
        if (typeof audio.fadeOut === 'function' && !options.immediate) {
          audio.fadeOut(350);
        } else {
          audio.stop();
        }
      }
      currentTrack = '';
      isPlaying = false;
      return getSnapshot();
    }

    // TITLE or TITLE_SUB
    const wantTrack = desiredTrackForTitle();
    if (!wantTrack) {
      if (isPlaying || currentTrack) audio.stop();
      currentTrack = '';
      isPlaying = false;
      return getSnapshot();
    }

    const wasTitle = prevState === SCREEN_STATES.TITLE || prevState === SCREEN_STATES.TITLE_SUB;
    const sameTrack = isPlaying && currentTrack === wantTrack;

    // Co-share across TITLE <-> TITLE_SUB without restarting or stacking
    if (wasTitle && sameTrack && !options.forceRestart) {
      return getSnapshot();
    }

    if (isPlaying && currentTrack !== wantTrack) {
      audio.stop();
    }
    currentTrack = wantTrack;
    isPlaying = true;
    playStartCount += 1;
    audio.play(wantTrack, true);
    return getSnapshot();
  }

  function setTrueUnlocked(unlocked) {
    trueUnlocked = !!unlocked;
    if (screenState === SCREEN_STATES.TITLE || screenState === SCREEN_STATES.TITLE_SUB) {
      return transition(screenState, { trueUnlocked });
    }
    return getSnapshot();
  }

  function setBgmEnabled(enabled) {
    bgmEnabled = !!enabled;
    return transition(screenState, { bgmEnabled });
  }

  function adoptExternalTrack(trackSrc) {
    currentTrack = trackSrc || '';
    isPlaying = !!trackSrc;
    return getSnapshot();
  }

  function getSnapshot() {
    return {
      screenState,
      currentTrack,
      isPlaying,
      playStartCount,
      trueUnlocked,
      bgmEnabled,
    };
  }

  return {
    SCREEN_STATES,
    transition,
    setTrueUnlocked,
    setBgmEnabled,
    adoptExternalTrack,
    getSnapshot,
  };
}

module.exports = {
  SCREEN_STATES,
  createTitleMusicController,
};
