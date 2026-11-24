const previewAudio = document.querySelector('#preview-audio');
const previewSound = document.querySelector('#preview-sound');
const previewAudioStatus = document.querySelector('#audio-status');
previewAudio.volume = 0.5;

let previewEnabled = false;
let previewState = { playing: false, revision: 0, position: 0 };
let previewRevision = -1;
let previewBusy = false;

const TRACK_LABELS = {
  title: '正在播放原作标题曲（bgm36）',
  true: '正在播放真相篇标题曲（bgm33 · 青鸟）',
  opening: '正在播放原作 OP 主题曲',
};

function updateSoundLabel() {
  previewSound.textContent = previewEnabled ? '预览声音：开启' : '启用预览声音';
}

function stopPreviewAudio() {
  previewAudio.pause();
  if (previewAudio.readyState) previewAudio.currentTime = 0;
  previewRevision = -1;
}

async function applyPreviewSound() {
  if (!previewEnabled || !previewState.playing || !previewState.source) {
    stopPreviewAudio();
    previewAudioStatus.textContent = previewEnabled ? '当前场景静音' : '点击“启用预览声音”同步播放原作 BGM/OP';
    return;
  }
  try {
    const src = '/app-audio/' + encodeURIComponent(previewState.source.replace('/common/', ''));
    if (!previewAudio.src || !previewAudio.src.endsWith(src)) previewAudio.src = src;
    previewAudio.loop = previewState.loop !== false;
    let pos = (previewState.position || 0) + (previewState.updatedAt ? Math.max(0, Date.now() - previewState.updatedAt) / 1000 : 0);
    if (previewState.duration > 0) {
      pos = previewAudio.loop ? pos % previewState.duration : Math.min(pos, previewState.duration);
    }
    if (previewRevision !== previewState.revision) {
      previewRevision = previewState.revision;
      previewAudio.currentTime = pos;
    } else if (Math.abs(previewAudio.currentTime - pos) > 1.5) {
      previewAudio.currentTime = pos;
    }
    await previewAudio.play();
    previewAudioStatus.textContent = TRACK_LABELS[previewState.track] || '正在播放原作 BGM';
  } catch (e) {
    previewAudioStatus.textContent = '请点击“启用预览声音”以允许浏览器播放';
    previewEnabled = false;
    updateSoundLabel();
  }
}

previewSound.addEventListener('click', () => {
  previewEnabled = !previewEnabled;
  updateSoundLabel();
  applyPreviewSound();
});

async function refreshPreviewSound() {
  if (previewBusy) return;
  previewBusy = true;
  try {
    const r = await fetch('/audio-state');
    if (!r.ok) throw Error('audio-state');
    previewState = await r.json();
    await applyPreviewSound();
  } catch (e) {
    stopPreviewAudio();
    previewAudioStatus.textContent = '模拟器音频状态连接中…';
  } finally {
    previewBusy = false;
  }
}

window.addEventListener('pagehide', stopPreviewAudio);
setInterval(refreshPreviewSound, 450);
refreshPreviewSound();
