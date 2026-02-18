/* codigos-checkbox.js
 * SOLO convierte #id_codigos_actividad en dropdown con checkboxes.
 * Muestra solo el CONTEO en el cabezal (sin nombres).
 * No toca otros filtros ni JS.
 */
(function () {
  function $(id) { return document.getElementById(id); }

  function buildUI(selectEl) {
    // si ya existe, no duplicar
    let dd = selectEl.nextElementSibling;
    if (dd && dd.classList && dd.classList.contains("ls-dd")) return dd;

    dd = document.createElement("div");
    dd.id = "codigos-dd";                 // id para estilos específicos si querés
    dd.className = "ls-dd";
    dd.innerHTML = `
      <button type="button" class="ls-head" title="Seleccione PRUEBA…">
        <span class="ls-placeholder">Seleccione PRUEBA…</span>
        <span class="ls-counter"></span>
        <span class="ls-caret">▾</span>
      </button>
      <div class="ls-panel">
        <div class="ls-grid"></div>
      </div>
    `;
    selectEl.insertAdjacentElement("afterend", dd);
    return dd;
  }

  // Solo conteo (sin nombres)
  function updateHead(dd, selectEl) {
    const head = dd.querySelector(".ls-head");
    const ph   = dd.querySelector(".ls-placeholder");
    const cnt  = dd.querySelector(".ls-counter");

    const n = selectEl.selectedOptions.length;

    if (!n) {
      ph.textContent = "Seleccione códigos…";
      cnt.textContent = "";
      head.title = "Seleccione códigos…";
      return;
    }

    // Mostrar únicamente el número de seleccionados
    ph.textContent = `${n} seleccionados`;
    cnt.textContent = "";           // no usamos el span .ls-counter
    head.title = `${n} seleccionados`;
  }

  function rebuildFromSelect(dd, selectEl) {
    const grid = dd.querySelector(".ls-grid");
    grid.innerHTML = "";

    const opts = Array.from(selectEl.options);
    if (!opts.length) { updateHead(dd, selectEl); return; }

    opts.forEach(opt => {
      const row = document.createElement("label");
      row.className = "ls-item";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = String(opt.value);
      cb.checked = !!opt.selected;
      cb.addEventListener("change", () => {
        // sincroniza con el <select multiple> (lo que se envía en el form)
        opt.selected = cb.checked;
        updateHead(dd, selectEl);
        selectEl.dispatchEvent(new Event("change", { bubbles: true }));
      });

      const span = document.createElement("span");
      span.textContent = opt.textContent;

      row.appendChild(cb);
      row.appendChild(span);
      grid.appendChild(row);
    });

    updateHead(dd, selectEl);
  }

  function wireOpenClose(dd) {
    const head = dd.querySelector(".ls-head");
    head.addEventListener("click", (e) => {
      e.stopPropagation();
      dd.classList.toggle("open");
    });
    // cerrar al click afuera
    document.addEventListener("click", (e) => {
      if (!dd.contains(e.target)) dd.classList.remove("open");
    });
  }

    function init() {
    ["id_codigos_actividad", "id_eett_subunidad"].forEach(function (id) {
      const selectEl = $(id);
      if (!selectEl) return;

      // ocultamos el select original
      selectEl.style.display = "none";

      const dd = buildUI(selectEl);
      wireOpenClose(dd);

      // reconstruir cuando AJAX repuebla las <option>
      const mo = new MutationObserver(() => rebuildFromSelect(dd, selectEl));
      mo.observe(selectEl, { childList: true });

      // reconstruir si cambian selecciones programáticamente
      selectEl.addEventListener("change", () => updateHead(dd, selectEl));

      // primera construcción
      rebuildFromSelect(dd, selectEl);
    });
  }


  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
