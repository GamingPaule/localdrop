const DEVICE_ID = (() => {
  let id = localStorage.getItem('ld_device_id');
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('ld_device_id', id); }
  return id;
})();

const DEVICE_NAME = (() => {
  let name = localStorage.getItem('ld_device_name');
  if (!name) {
    name = prompt('Wie soll dieses Gerät heißen?', /Android|iPhone|iPad/i.test(navigator.userAgent) ? 'Handy' : 'PC') || 'Gerät';
    localStorage.setItem('ld_device_name', name);
  }
  return name;
})();

const KIND = /Android|iPhone|iPad/i.test(navigator.userAgent) ? 'mobile' : 'pc';

const $bubbles  = document.getElementById('bubbles');
const $incoming = document.getElementById('incoming');
const $status   = document.getElementById('status');

let ws = null;
let reconnectTimer = null;

function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/${DEVICE_ID}`);

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'register', name: DEVICE_NAME, kind: KIND }));
    $status.textContent = 'Online als ' + DEVICE_NAME;
    $status.className = 'online';
    clearTimeout(reconnectTimer);
  };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'devices') renderBubbles(msg.devices.filter(d => d.id !== DEVICE_ID));
    if (msg.type === 'incoming') showIncoming(msg);
  };

  ws.onclose = () => {
    $status.textContent = 'Verbindung unterbrochen — versuche erneut...';
    $status.className = '';
    reconnectTimer = setTimeout(connect, 3000);
  };
}

function renderBubbles(devices) {
  $bubbles.innerHTML = '';
  if (devices.length === 0) {
    $bubbles.innerHTML = '<p class="empty">Keine anderen Geräte online.<br>Öffne LocalDrop auf einem anderen Gerät.</p>';
    return;
  }
  devices.forEach(dev => {
    const el = document.createElement('div');
    el.className = 'bubble';
    el.dataset.id = dev.id;
    el.innerHTML = `
      <div class="bubble-ring">${dev.kind === 'pc' ? '💻' : '📱'}</div>
      <div class="bubble-name">${escHtml(dev.name)}</div>
    `;
    el.addEventListener('click', () => pickAndSend(dev.id, dev.name, el));
    el.addEventListener('dragover', e => { e.preventDefault(); el.classList.add('drag-over'); });
    el.addEventListener('dragleave', () => el.classList.remove('drag-over'));
    el.addEventListener('drop', e => {
      e.preventDefault();
      el.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) sendFile(file, dev.id, dev.name, el);
    });
    $bubbles.appendChild(el);
  });
}

function pickAndSend(targetId, targetName, bubbleEl) {
  const input = document.createElement('input');
  input.type = 'file';
  input.onchange = () => { if (input.files[0]) sendFile(input.files[0], targetId, targetName, bubbleEl); };
  input.click();
}

async function sendFile(file, targetId, targetName, bubbleEl) {
  bubbleEl.classList.add('sending');
  const form = new FormData();
  form.append('file', file);
  form.append('target', targetId);
  form.append('from_name', DEVICE_NAME);
  try {
    const r = await fetch('/upload', { method: 'POST', body: form });
    if (!r.ok) throw new Error(`Server ${r.status}`);
    bubbleEl.classList.remove('sending');
    bubbleEl.classList.add('done');
    setTimeout(() => bubbleEl.classList.remove('done'), 2200);
  } catch (err) {
    bubbleEl.classList.remove('sending');
    alert('Fehler beim Senden: ' + err.message);
  }
}

function showIncoming(msg) {
  if (Notification.permission === 'granted') {
    new Notification('LocalDrop — Datei empfangen', {
      body: `${escHtml(msg.from)}: ${escHtml(msg.filename)}`,
      icon: '/static/icon-192.png',
    });
  }
  const banner = document.createElement('div');
  banner.className = 'incoming-banner';
  banner.innerHTML = `
    <span>📥 <strong>${escHtml(msg.from)}</strong>: ${escHtml(msg.filename)}</span>
    <a class="download-btn"
       href="/download/${encodeURIComponent(msg.file_id)}"
       download="${escHtml(msg.filename)}">Herunterladen</a>
  `;
  $incoming.prepend(banner);
  setTimeout(() => banner.remove(), 60000);
}

function escHtml(str) {
  return String(str).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

if (Notification.permission === 'default') Notification.requestPermission();

connect();
