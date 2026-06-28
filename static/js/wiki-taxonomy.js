/** Quick category creation and tag autocomplete on create/edit wiki forms */
(function () {
  'use strict';

  const cfg = window.WIKI_TAXONOMY || {};
  const quickCategoryUrl = cfg.quickCategoryUrl || '/wiki/api/categories/quick/';
  const tagSuggestUrl = cfg.tagSuggestUrl || '/wiki/api/tags/suggest/';

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  async function quickCreateCategory() {
    const nameInput = document.getElementById('new_category_name');
    const categorySelect = document.getElementById('category');
    const status = document.getElementById('quick-category-status');
    const btn = document.getElementById('quick-category-btn');
    const name = nameInput?.value?.trim();
    if (!name) {
      if (status) {
        status.textContent = 'Enter a category name first.';
        status.classList.remove('hidden');
      }
      return;
    }
    if (btn) btn.disabled = true;
    try {
      const res = await fetch(quickCategoryUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Could not create category');
      if (categorySelect) {
        const option = document.createElement('option');
        option.value = String(data.id);
        option.textContent = data.name;
        option.selected = true;
        categorySelect.appendChild(option);
      }
      if (nameInput) nameInput.value = '';
      if (status) {
        status.textContent = `Category “${data.name}” created and selected.`;
        status.classList.remove('hidden', 'text-destructive');
      }
    } catch (err) {
      if (status) {
        status.textContent = err.message || 'Category creation failed';
        status.classList.remove('hidden');
        status.classList.add('text-destructive');
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  let tagTimer = null;
  async function refreshTagSuggestions(query) {
    const datalist = document.getElementById('tag-suggestions');
    if (!datalist || !query || query.length < 1) return;
    const needle = query.split(/[,;]/).pop().trim();
    if (needle.length < 1) return;
    try {
      const res = await fetch(`${tagSuggestUrl}?q=${encodeURIComponent(needle)}&limit=12`);
      const data = await res.json();
      datalist.innerHTML = '';
      (data.tags || []).forEach((tag) => {
        const opt = document.createElement('option');
        opt.value = tag.name;
        datalist.appendChild(opt);
      });
    } catch (_) {
      /* ignore */
    }
  }

  document.getElementById('quick-category-btn')?.addEventListener('click', quickCreateCategory);

  const tagsInput = document.getElementById('tags');
  tagsInput?.addEventListener('input', () => {
    clearTimeout(tagTimer);
    tagTimer = setTimeout(() => refreshTagSuggestions(tagsInput.value), 200);
  });
})();
