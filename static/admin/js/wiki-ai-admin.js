(function () {
  'use strict';

  function getCsrfToken() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  function field(name) {
    return document.getElementById('id_' + name) || document.querySelector('[name="' + name + '"]');
  }

  function setStatus(msg, isError) {
    const el = document.getElementById('wiki-admin-ai-status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? '#b91c1c' : '';
  }

  async function runAssist(action) {
    const contentField = field('content');
    const titleField = field('title');
    const summaryField = field('summary');
    const text = contentField?.value?.trim() || '';
    if (!text) {
      setStatus('Add page content first.', true);
      return;
    }
    setStatus('Cerebras AI is working…');
    try {
      const res = await fetch('/api/ai/admin/assist/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          action,
          text,
          title: titleField?.value || '',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'AI assist failed');

      if (action === 'format' && data.markdown) {
        contentField.value = data.markdown;
        if (titleField && data.title && !titleField.value.trim()) titleField.value = data.title;
        if (summaryField && data.summary && !summaryField.value.trim()) summaryField.value = data.summary;
        setStatus('Content formatted — review and save.');
      } else if (action === 'summary' && data.summary) {
        if (summaryField) summaryField.value = data.summary;
        setStatus('Summary generated.');
      } else if (action === 'title' && data.title) {
        if (titleField) titleField.value = data.title;
        setStatus('Title suggested.');
      }
    } catch (err) {
      setStatus(err.message || 'Could not reach Cerebras AI', true);
    }
  }

  document.querySelectorAll('[data-wiki-ai-admin]').forEach((btn) => {
    btn.addEventListener('click', () => runAssist(btn.getAttribute('data-wiki-ai-admin')));
  });
})();
