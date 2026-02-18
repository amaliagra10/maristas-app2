document.addEventListener("DOMContentLoaded", function () {

  const formAdj = document.getElementById("form-adjunto");
  if (!formAdj) return; // seguridad por si el JS carga en otra página

  const lista = document.getElementById("adjuntos-list");

  const urlCrear = window.MI_APP_URLS.urlAdjuntoCrear;
  const urlBorrar = window.MI_APP_URLS.urlAdjuntoBorrar;
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  // ---------------------------------------------------------
  // SUBIR ADJUNTOS
  // ---------------------------------------------------------
  formAdj.addEventListener("submit", function (e) {
    e.preventDefault();

    let fd = new FormData(formAdj);

    fetch(urlCrear, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken
      },
      body: fd
    })
    .then(r => r.json())
    .then(resp => {

      if (!resp.ok) {
        alert("Error al subir archivos: " + JSON.stringify(resp.errors || resp.error));
        return;
      }

      // si estaba el mensaje "No hay adjuntos", se borra
      const noAdj = document.getElementById("no-adjuntos");
      if (noAdj) noAdj.remove();

      resp.adjuntos.forEach(a => {
        let li = document.createElement("li");
        li.dataset.id = a.id;
        li.style.marginBottom = "6px";
        console.log("CREANDO BOTÓN DEL JS !!!");
        li.innerHTML = `
          <a href="${a.url}" target="_blank" rel="noopener">${a.nombre}</a>
          <small> (${a.tamano} bytes)</small>
          ${a.descripcion ? `<small> — ${a.descripcion}</small>` : ""}
          <button type="button"
            class="btn-del"
            data-id="${a.id}"
            title="Eliminar adjunto">X</button>
        `;
        lista.appendChild(li);
      });

      // reset del form
      formAdj.reset();
      document.getElementById("id_adjuntos").value = "";
    })
    .catch(err => {
      alert("Error inesperado subiendo archivos.");
      console.error(err);
    });
  });

  // ---------------------------------------------------------
  // BORRAR ADJUNTO
  // ---------------------------------------------------------
  lista.addEventListener("click", function (e) {
    if (!e.target.classList.contains("btn-del")) return;

    const adjuntoId = e.target.dataset.id;
    const obraId = document.querySelector("input[name='obra_id']").value;

    if (!confirm("¿Eliminar este adjunto?")) return;

    let fd = new FormData();
    fd.append("adjunto_id", adjuntoId);
    fd.append("obra_id", obraId);

    fetch(urlBorrar, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken
      },
      body: fd
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.ok) {
        // Eliminar del DOM solo si el servidor confirma
        const li = lista.querySelector(`li[data-id='${adjuntoId}']`);
        if (li) li.remove();

        if (lista.children.length === 0) {
          lista.innerHTML = `<li id="no-adjuntos">No hay adjuntos aún.</li>`;
        }
      } else {
        alert("No se pudo eliminar el adjunto: " + (resp.error || "Error desconocido"));
      }
    })
    .catch(err => {
      alert("Error inesperado eliminando archivo.");
      console.error(err);
    });
  });

});
