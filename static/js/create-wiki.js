/** Notion-style quick wiki create — EasyMDE, inline media upload, cover preview */
(function () {
  'use strict';

  const form = document.getElementById('create-wiki-form');
  if (!form) return;

  const cfg = window.WIKI_CREATE || {};
  const uploadUrl = cfg.uploadUrl || '/wiki/api/upload/';

  const textarea = document.getElementById('content');
  const titleInput = document.getElementById('title');
  const summaryInput = document.getElementById('summary');
  const mediaInput = document.getElementById('media_files');
  const coverInput = document.getElementById('cover_image');
  const coverBanner = document.getElementById('cover-banner');
  const coverPreviewImg = document.getElementById('cover-preview-img');
  const coverLabel = document.getElementById('cover-label');
  const pasteHint = document.getElementById('paste-hint');
  const uploadStatus = document.getElementById('upload-status');
  const aiBtn = document.getElementById('ai-format-btn');
  const aiStatus = document.getElementById('ai-status');
  const wikiPasteBtn = document.getElementById('wikipedia-paste-btn');
  const wikiPasteStatus = document.getElementById('wikipedia-paste-status');
  const wikiSourceUrl = document.getElementById('wikipedia_source_url');
  const wikiImportBtn = document.getElementById('wikipedia-import-btn');
  const wikiImportStatus = document.getElementById('wikipedia-import-status');
  const wikiUrlInput = document.getElementById('wikipedia_url');
  const wikiDownloadMedia = document.getElementById('wikipedia_download_media');
  const wikiPasteUrl = cfg.pasteWikipediaUrl || '/wiki/api/paste-wikipedia/';
  const wikiImportUrl = cfg.importWikipediaUrl || '/wiki/api/import-wikipedia/';
  const videoInput = document.getElementById('editor-video-input');
  const audioInput = document.getElementById('editor-audio-input');
  const imageInput = document.getElementById('editor-image-input');
  const pdfInput = document.getElementById('editor-pdf-input');

  let editor = null;

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function contentValue() {
    return editor ? editor.value() : textarea?.value || '';
  }

  function setContentValue(val) {
    if (editor) editor.value(val);
    else if (textarea) textarea.value = val;
    pasteHint?.classList.remove('hidden');
  }

  function insertAtCursor(snippet) {
    if (editor?.codemirror) {
      const cm = editor.codemirror;
      const pos = cm.getCursor();
      cm.replaceRange(`\n\n${snippet}\n\n`, pos);
      cm.focus();
    } else if (textarea) {
      textarea.value += `\n\n${snippet}\n\n`;
    }
    pasteHint?.classList.remove('hidden');
  }

  function setStatus(el, msg, isError) {
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hidden', 'text-destructive', 'text-muted-foreground');
    el.classList.add(isError ? 'text-destructive' : 'text-muted-foreground');
  }

  async function uploadFile(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(uploadUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCsrfToken() },
      body: fd,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed');
    return data;
  }

  async function handleMediaUpload(file, label) {
    if (!file) return;
    setStatus(uploadStatus, `Uploading ${label || file.name}…`);
    try {
      const data = await uploadFile(file);
      insertAtCursor(data.markdown);
      setStatus(uploadStatus, `${label || file.name} inserted.`);
    } catch (err) {
      setStatus(uploadStatus, err.message || 'Upload failed', true);
    }
  }

  async function formatWikipediaPaste(textOverride) {
    const text = (textOverride || contentValue()).trim();
    if (!text) {
      setStatus(wikiPasteStatus, 'Paste Wikipedia article text first.', true);
      return;
    }
    if (wikiPasteBtn) wikiPasteBtn.disabled = true;
    setStatus(wikiPasteStatus, 'Formatting Wikipedia paste with citations and wiki links…');

    try {
      const res = await fetch(wikiPasteUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          text,
          source_url: wikiSourceUrl?.value?.trim() || '',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Wikipedia paste failed');
      setContentValue(data.markdown || '');
      if (titleInput && data.title && !titleInput.value.trim()) {
        titleInput.value = data.title;
      }
      setStatus(
        wikiPasteStatus,
        `Formatted with ${data.citation_count || 0} citations and internal wiki links.`,
      );
    } catch (err) {
      setStatus(wikiPasteStatus, err.message || 'Could not format Wikipedia paste', true);
    } finally {
      if (wikiPasteBtn) wikiPasteBtn.disabled = false;
    }
  }

  async function importWikipediaUrl() {
    const url = wikiUrlInput?.value?.trim();
    if (!url) {
      setStatus(wikiImportStatus, 'Enter a Wikipedia article URL.', true);
      return;
    }
    if (wikiImportBtn) wikiImportBtn.disabled = true;
    setStatus(wikiImportStatus, 'Fetching and formatting from Wikipedia…');

    try {
      const res = await fetch(wikiImportUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          url,
          download_media: Boolean(wikiDownloadMedia?.checked),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Wikipedia import failed');
      setContentValue(data.markdown || '');
      if (titleInput && data.title && !titleInput.value.trim()) {
        titleInput.value = data.title;
      }
      if (summaryInput && data.summary && !summaryInput.value.trim()) {
        summaryInput.value = data.summary;
      }
      setStatus(
        wikiImportStatus,
        `Imported “${data.title}” — ${data.section_count || 0} sections, ${data.media_count || 0} media, ${data.citation_count || 0} citations.`,
      );
    } catch (err) {
      setStatus(wikiImportStatus, err.message || 'Could not import from Wikipedia', true);
    } finally {
      if (wikiImportBtn) wikiImportBtn.disabled = false;
    }
  }

  if (textarea && window.EasyMDE) {
    editor = new EasyMDE({
      element: textarea,
      autofocus: true,
      spellChecker: false,
      minHeight: '320px',
      status: ['lines', 'words', 'upload'],
      placeholder: 'Write markdown, paste content, or drop media here…',
      imageUploadFunction: (file, onSuccess, onError) => {
        uploadFile(file)
          .then((data) => {
            if (data.type === 'image' || data.type === 'gif') {
              onSuccess(data.url);
            } else {
              insertAtCursor(data.markdown);
            }
            setStatus(uploadStatus, `${file.name} uploaded.`);
          })
          .catch((err) => onError(err.message));
      },
      toolbar: [
        'bold', 'italic', 'heading', '|',
        'quote', 'unordered-list', 'ordered-list', '|',
        'link', '|',
        {
          name: 'upload-image',
          action: () => imageInput?.click(),
          className: 'editor-tool-image',
          title: 'Upload image',
        },
        {
          name: 'upload-video',
          action: () => videoInput?.click(),
          className: 'editor-tool-video',
          title: 'Upload video',
        },
        {
          name: 'upload-audio',
          action: () => audioInput?.click(),
          className: 'editor-tool-audio',
          title: 'Upload audio',
        },
          {
            name: 'upload-pdf',
            action: () => pdfInput?.click(),
            className: 'editor-tool-pdf',
            title: 'Upload PDF',
          },
          {
            name: 'wikipedia-import',
            action: () => importWikipediaUrl(),
            className: 'editor-tool-wikipedia-import',
            title: 'Import from Wikipedia URL',
          },
          {
            name: 'wikipedia-paste',
            action: () => formatWikipediaPaste(),
            className: 'editor-tool-wikipedia',
            title: 'Format Wikipedia paste',
          },
          '|',
        'preview', 'side-by-side', 'fullscreen',
      ],
    });

    const cmEl = editor.codemirror?.getWrapperElement?.();
    if (cmEl) {
      cmEl.addEventListener('dragover', (e) => e.preventDefault());
      cmEl.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer?.files || []);
        files.forEach((f) => handleMediaUpload(f));
      });
    }
  }

  imageInput?.addEventListener('change', () => {
    handleMediaUpload(imageInput.files?.[0], 'Image');
    imageInput.value = '';
  });

  videoInput?.addEventListener('change', () => {
    handleMediaUpload(videoInput.files?.[0], 'Video');
    videoInput.value = '';
  });

  audioInput?.addEventListener('change', () => {
    handleMediaUpload(audioInput.files?.[0], 'Audio');
    audioInput.value = '';
  });

  pdfInput?.addEventListener('change', () => {
    handleMediaUpload(pdfInput.files?.[0], 'PDF');
    pdfInput.value = '';
  });

  coverInput?.addEventListener('change', () => {
    const file = coverInput.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    if (coverPreviewImg) {
      coverPreviewImg.src = url;
      coverPreviewImg.classList.remove('hidden');
    }
    coverBanner?.classList.remove('notion-cover--empty');
    coverBanner?.classList.add('notion-cover--filled');
    if (coverLabel) coverLabel.textContent = 'Change cover';
  });

  async function formatWithAI() {
    const text = contentValue().trim();
    if (!text) {
      setStatus(aiStatus, 'Write some content first.', true);
      return;
    }
    if (aiBtn) {
      aiBtn.disabled = true;
    }
    setStatus(aiStatus, 'Cerebras AI is structuring your page…');

    try {
      const res = await fetch('/api/ai/format/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          text,
          title: titleInput?.value?.trim() || '',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'AI format failed');
      setContentValue(data.markdown || '');
      if (titleInput && data.title && !titleInput.value.trim()) {
        titleInput.value = data.title;
      }
      if (summaryInput && data.summary && !summaryInput.value.trim()) {
        summaryInput.value = data.summary;
      }
      setStatus(aiStatus, `Formatted with ${data.model || 'Cerebras'}. Review and save.`);
    } catch (err) {
      setStatus(aiStatus, err.message || 'Could not reach Cerebras AI', true);
    } finally {
      if (aiBtn) aiBtn.disabled = false;
    }
  }

  aiBtn?.addEventListener('click', formatWithAI);

  wikiPasteBtn?.addEventListener('click', () => formatWikipediaPaste());
  wikiImportBtn?.addEventListener('click', () => importWikipediaUrl());

  document.addEventListener('paste', (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          handleMediaUpload(file);
        }
      } else if (item.type === 'text/plain') {
        item.getAsString((text) => {
          if (text && text.length > 40 && !contentValue().trim()) {
            setContentValue(text);
          }
          if (text && /\[\d{1,3}\]/.test(text) && text.length > 400) {
            setStatus(wikiPasteStatus, 'Wikipedia-style paste detected — click “Format Wikipedia” to add citations.');
          }
        });
      }
    }
  });

  mediaInput?.addEventListener('change', () => {
    if (mediaInput.files?.length) {
      setStatus(uploadStatus, `${mediaInput.files.length} file(s) will attach when you save.`);
    }
  });

  form.addEventListener('submit', () => {
    if (editor && textarea) textarea.value = editor.value();
  });
})();
