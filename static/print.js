// Print button on the printable summaries (inline onclick is blocked by the Content-Security-Policy).
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-print]")) window.print();
});
