document.addEventListener('DOMContentLoaded', function () {
  try {
    var els = document.querySelectorAll('.markdown-editor');
    els.forEach(function (el) {
      if (!el._simplemde) {
        // eslint-disable-next-line no-undef
        var sm = new SimpleMDE({ element: el, spellChecker: false, status: false });
        el._simplemde = sm;
      }
    });
  } catch (e) {
    // Fail silently in admin if SimpleMDE isn't available
    console.error('SimpleMDE init failed', e);
  }
});
