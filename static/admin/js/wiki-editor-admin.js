/** EasyMDE + media upload toolbar for WikiPage admin content field */
(function () {
  'use strict';

  const textarea = document.getElementById('id_content');
  if (!textarea || !window.EasyMDE) return;

  const uploadUrl = '/wiki/api/upload/';

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  async function upload(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(uploadUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrf() },
      body: fd,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed');
    return data;
  }

  function insert(md) {
    const cm = editor.codemirror;
    const pos = cm.getCursor();
    cm.replaceRange(`\n\n${md}\n\n`, pos);
  }

  function pick(accept, handler) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;
    input.hidden = true;
    document.body.appendChild(input);
    input.addEventListener('change', () => {
      const file = input.files?.[0];
      if (file) handler(file);
      input.remove();
    });
    input.click();
  }

  const editor = new EasyMDE({
    element: textarea,
    spellChecker: false,
    minHeight: '360px',
    toolbar: [
      'bold', 'italic', 'heading', '|',
      'quote', 'unordered-list', 'ordered-list', '|',
      'link', '|',
      {
        name: 'upload-image',
        action: () => pick('image/*', (f) => upload(f).then((d) => insert(d.markdown)).catch(alert)),
        className: 'editor-tool-image',
        title: 'Upload image',
      },
      {
        name: 'upload-video',
        action: () => pick('video/*', (f) => upload(f).then((d) => insert(d.markdown)).catch(alert)),
        className: 'editor-tool-video',
        title: 'Upload video',
      },
      {
        name: 'upload-audio',
        action: () => pick('audio/*', (f) => upload(f).then((d) => insert(d.markdown)).catch(alert)),
        className: 'editor-tool-audio',
        title: 'Upload audio',
      },
      {
        name: 'upload-pdf',
        action: () => pick('.pdf', (f) => upload(f).then((d) => insert(d.markdown)).catch(alert)),
        className: 'editor-tool-pdf',
        title: 'Upload PDF',
      },
      '|', 'preview', 'side-by-side', 'fullscreen',
    ],
  });

  const form = textarea.closest('form');
  form?.addEventListener('submit', () => {
    textarea.value = editor.value();
  });
})();
