function initTableFilter(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;
  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    table.querySelectorAll('tbody tr').forEach(r => {
      r.style.display = !q || r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-filter-table]').forEach(inp => {
    initTableFilter(inp.id, inp.getAttribute('data-filter-table'));
  });
});
