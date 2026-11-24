'use strict';

exports.makeAudioMonitor = function (now = () => Date.now()) {
  let pending = '';
  const state = {
    playing: false,
    track: '',
    source: '',
    loop: false,
    revision: 0,
    position: 0,
    duration: 0,
    updatedAt: now(),
  };

  return {
    get() {
      return Object.assign({}, state);
    },
    feed(chunk) {
      pending += chunk;
      const lines = pending.split('\n');
      pending = lines.pop().slice(-12000);
      for (const line of lines) {
        if (/system_audio_wrap_pause|system_audio_wrap_stop|audio_media_player_pause|audio_media_player_stop|audio_media_player_reset|audio_media_player_release/.test(line)) {
          state.playing = false;
          state.position = 0;
          state.updatedAt = now();
        }
        const mOpen = line.match(/(title-bgm\.opus|title-true-bgm\.opus|opening-bgm\.opus)/);
        if (mOpen) {
          const fname = mOpen[1];
          state.playing = true;
          state.revision++;
          state.track = fname.includes('opening') ? 'opening' : (fname.includes('true') ? 'true' : 'title');
          state.source = '/common/' + fname;
          state.loop = state.track !== 'opening';
          state.position = 0;
          state.updatedAt = now();
        }
        const q = line.match(/audio_media_player_query_cb\(\),volume:\d+ position:(\d+) duration:(\d+)/);
        if (q && state.playing) {
          state.position = Number(q[1]) / 1000;
          if (Number(q[2]) > 0) state.duration = Number(q[2]) / 1000;
          state.updatedAt = now();
        }
      }
    },
  };
};
