// Live Markdown preview. The server renders and sanitizes (POST /admin/preview);
// this only swaps the returned HTML into the box. Without JavaScript the box
// keeps its server-rendered content.
(function () {
  var form = document.querySelector('form[data-preview-url]');
  var box = document.getElementById('preview');
  if (!form || !box || !window.fetch) return;
  var area = form.querySelector('textarea[name="body_md"]');
  var token = form.querySelector('input[name="csrf_token"]').value;
  var timer = null, latest = 0, inflight = null;
  var note = document.createElement('p');
  note.className = 'error';
  note.hidden = true;
  box.parentNode.insertBefore(note, box);
  function fail(message) { note.textContent = message; note.hidden = false; }
  function refresh() {
    var n = ++latest;
    if (inflight) inflight.abort();
    inflight = window.AbortController ? new AbortController() : null;
    fetch(form.dataset.previewUrl, {
      method: 'POST',
      credentials: 'same-origin',
      redirect: 'manual',
      signal: inflight ? inflight.signal : undefined,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({body_md: area.value, csrf_token: token})
    }).then(function (r) {
      if (r.type === 'opaqueredirect') { fail('Your session ended. Log in again in another tab, then reload this page.'); return null; }
      if (r.ok) return r.text();
      fail(r.status === 403 ? 'Preview stopped: this page is out of date. Reload it (unsaved text is kept only until you do).'
                            : 'Preview unavailable.');
      return null;
    }).then(function (html) {
      if (html !== null && n === latest) { note.hidden = true; box.innerHTML = html; }
    }).catch(function (e) {
      if (e.name !== 'AbortError') fail('Preview unavailable.');
    });
  }
  area.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(refresh, 250); });
  if (!box.innerHTML.trim() && area.value) refresh();
})();
