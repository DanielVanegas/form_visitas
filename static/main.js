// Elimina ?exito=1 después de mostrar el mensaje (si existe en la URL)
if (window.location.search.includes("exito=1")) {
  const url = new URL(window.location);
  url.searchParams.delete("exito");
  window.history.replaceState({}, document.title, url.pathname);
}

// Inicializa los selects de Materialize al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
  var elems = document.querySelectorAll('select');
  if (typeof M !== 'undefined' && M.FormSelect) {
    M.FormSelect.init(elems);
  }
});

// Elimina el mensaje de éxito después de 5 segundos
setTimeout(() => {
  const mensaje = document.getElementById("mensaje-exito");
  if (mensaje) {
    mensaje.style.transition = "opacity 0.5s ease";
    mensaje.style.opacity = 0;
    setTimeout(() => mensaje.remove(), 500);  // Remueve el nodo después de desvanecerse
  }
}, 5000);
