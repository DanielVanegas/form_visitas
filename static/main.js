// Elimina ?exito=1 después de mostrar el mensaje (si existe en la URL)
if (window.location.search.includes("exito=1")) {
  const url = new URL(window.location);
  url.searchParams.delete("exito");
  window.history.replaceState({}, document.title, url.pathname);
}

// Inicializa los selects de Materialize al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar selects
  var elems = document.querySelectorAll('select');
  if (typeof M !== 'undefined' && M.FormSelect) {
    M.FormSelect.init(elems);
  }
  // Mostrar/ocultar sección de más información
  const chkMasInfo = document.getElementById("mas_info");
  const bloqueMasInfo = document.getElementById("bloque_mas_info");
  if (chkMasInfo && bloqueMasInfo) {
    chkMasInfo.addEventListener("change", function() {
      bloqueMasInfo.style.display = this.checked ? "block" : "none";
    });
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

// Aplica modo oscuro si ya está guardado
if (localStorage.getItem('darkMode') === '1') {
  document.body.classList.add('dark-mode');
}

document.getElementById("modo-oscuro").addEventListener("click", function() {
  document.body.classList.toggle("dark-mode");
  localStorage.setItem('darkMode', document.body.classList.contains("dark-mode") ? '1' : '0');
});

function updateDarkModeIcon() {
  document.getElementById("modo-oscuro").querySelector("span")
    .textContent = document.body.classList.contains("dark-mode") ? "light_mode" : "dark_mode";
}

// Llama al inicio y cada vez que se haga click
updateDarkModeIcon();
document.getElementById("modo-oscuro").addEventListener("click", function() {
  updateDarkModeIcon();
});


$(document).ready(function () {
  M.Tooltip.init(document.querySelectorAll('.tooltipped'));
  const tablaElement = $('#tablaDashboard');
  if (!tablaElement.length) return;

  // Asignar data-order como timestamp a la columna Fecha Visita
  $('#tablaDashboard td:nth-child(3)').each(function() {
      const text = $(this).text().trim();
      if (text === "") {
          // Si está vacío, le damos un timestamp muy alto para que quede primero en DESC
          $(this).attr("data-order", 99999999999999);
      } else {
          // Convertimos la fecha a timestamp para ordenar correctamente
          $(this).attr("data-order", new Date(text).getTime());
      }
  });

  const tabla = tablaElement.DataTable({
    paging: false,
    order: [[2, "desc"], [3, "desc"]], // 2=Fecha Visita, 3=Hora Visita
    orderMulti: true,
    orderCellsTop: true,
    stateSave: false,
    language: {
      url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
    },
    initComplete: function () {
      this.api().columns().every(function () {
        var that = this;
        $('input', this.header()).on('keyup change clear', function () {
          if (that.search() !== this.value) {
            that.search(this.value).draw();
          }
        });
      });
    }
  });

  // 🖊️ Editar celdas (Material Design)
  tablaElement.on('click', '.edit-btn', function () {
    const tr = $(this).closest('tr');
    tr.find('[data-campo]').attr('contenteditable', true).addClass('editable');
    tr.addClass('modo-edicion');
    tr.find('.edit-btn').hide();
    tr.find('.save-btn').show();
  });

  // 💾 Guardar cambios (Material Design)
  tablaElement.on('click', '.save-btn', function () {
    const tr = $(this).closest('tr');
    const consecutivo = tr.find('td:first').text().trim();

    tr.find('[data-campo]').each(function () {
      const td = $(this);
      const campo = td.data('campo');
      const valor = td.text().trim();
      fetch('/update-asignacion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consecutivo, campo, valor })
      }).then(r => {
        if (!r.ok) alert("❌ Error al guardar cambio.");
      });
    });

    tr.find('[data-campo]').removeAttr('contenteditable').removeClass('editable');
    tr.removeClass('modo-edicion');
    tr.find('.save-btn').hide();
    tr.find('.edit-btn').show();
  });

  // 🔍 Buscador global con lupa (con clase visible animada)
  const toggleBtn = document.getElementById("toggle-buscador");
  const input = document.getElementById("buscador-global");

  if (toggleBtn && input) {
    toggleBtn.addEventListener("click", () => {
      const isVisible = input.classList.contains("visible");

      if (isVisible) {
        input.classList.remove("visible");
        input.value = "";
        tabla.search("").draw();
      } else {
        input.classList.add("visible");
        input.focus();
      }
    });

    input.addEventListener("input", () => {
      tabla.search(input.value).draw();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        input.classList.remove("visible");
        input.value = "";
        tabla.search("").draw();
      }
    });
  }
});

