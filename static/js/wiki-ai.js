/** Wiki page AI — summarize and ask (10 free requests/day for non-staff). */
(function () {
  'use strict';

  const root = document.querySelector('[data-wiki-ai]');
  if (!root || root.dataset.aiConfigured !== 'true') return;

  const slug = root.dataset.pageSlug;
  const modal = document.getElementById('wiki-ai-modal');
  const modalTitle = modal?.querySelector('[data-ai-modal-title]');
  const askForm = modal?.querySelector('[data-ai-ask-form]');
  const questionInput = document.getElementById('wiki-ai-question');
  const loadingEl = modal?.querySelector('[data-ai-loading]');
  const errorEl = modal?.querySelector('[data-ai-error]');
  const resultEl = modal?.querySelector('[data-ai-result]');
  const quotaLabel = root.querySelector('[data-ai-quota-label]');
  const quotaFootnote = modal?.querySelector('[data-ai-quota-footnote]');

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function updateQuota(quota) {
    if (!quota || quota.unlimited) {
      if (quotaLabel) quotaLabel.textContent = '';
      if (quotaFootnote) quotaFootnote.textContent = 'Staff accounts have unlimited AI requests.';
      return;
    }
    if (quotaLabel) {
      quotaLabel.textContent = `${quota.remaining}/${quota.limit} AI today`;
    }
    if (quotaFootnote) {
      quotaFootnote.textContent = `${quota.remaining} of ${quota.limit} free AI requests remaining today.`;
    }
  }

  function openModal(mode) {
    if (!modal) return;
    errorEl?.classList.add('hidden');
    resultEl.innerHTML = '';
    loadingEl?.classList.add('hidden');
    askForm?.classList.toggle('hidden', mode !== 'ask');
    if (modalTitle) modalTitle.textContent = mode === 'ask' ? 'Ask about this page' : 'Page summary';
    modal.showModal();
  }

  function closeModal() {
    modal?.close();
  }

  function showLoading() {
    loadingEl?.classList.remove('hidden');
    errorEl?.classList.add('hidden');
    resultEl.innerHTML = '';
  }

  function showError(msg) {
    loadingEl?.classList.add('hidden');
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.classList.remove('hidden');
    }
  }

  function showResult(htmlish) {
    loadingEl?.classList.add('hidden');
    resultEl.innerHTML = simpleMarkdownToHtml(htmlish);
  }

  function simpleMarkdownToHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(.+)$/s, (m) => (m.includes('<ul>') || m.includes('<p>') ? m : `<p>${m}</p>`));
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      const err = new Error(data.error || 'AI request failed');
      err.quota = data.quota;
      throw err;
    }
    return data;
  }

  async function summarize() {
    openModal('summarize');
    showLoading();
    try {
      const data = await postJson('/api/ai/page/summarize/', { slug });
      showResult(data.summary);
      updateQuota(data.quota);
    } catch (err) {
      showError(err.message);
      if (err.quota) updateQuota(err.quota);
    }
  }

  async function ask() {
    const question = questionInput?.value?.trim();
    if (!question) {
      showError('Enter a question first.');
      return;
    }
    showLoading();
    try {
      const data = await postJson('/api/ai/page/ask/', { slug, question });
      showResult(data.answer);
      updateQuota(data.quota);
    } catch (err) {
      showError(err.message);
      if (err.quota) updateQuota(err.quota);
    }
  }

  root.querySelector('[data-ai-summarize]')?.addEventListener('click', summarize);
  root.querySelector('[data-ai-ask-open]')?.addEventListener('click', () => openModal('ask'));
  modal?.querySelector('[data-ai-modal-close]')?.addEventListener('click', closeModal);
  modal?.querySelector('[data-ai-ask-submit]')?.addEventListener('click', ask);
  modal?.addEventListener('cancel', (e) => {
    e.preventDefault();
    closeModal();
  });
})();
