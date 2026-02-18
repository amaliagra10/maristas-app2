// static/mi_app/actividad-staff.js
document.addEventListener('DOMContentLoaded', function () {

  const division = document.getElementById('id_division');
  const rama     = document.getElementById('id_rama');

  const contenedores = {
    entrenadores: document.getElementById('entrenadores-container'),
    ayudantes: document.getElementById('ayudantes-container'),
    pfs: document.getElementById('pfs-container'),
    managers: document.getElementById('managers-container')
  };

  function fillCheckboxContainer(container, items, name) {
    if (!container) return;
    container.innerHTML = '';
    items.forEach(item => {
      const label = document.createElement('label');
      label.className = 'checkbox-label';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.name = name;
      input.value = item.id;
      input.className = 'checkbox-input';
      label.appendChild(input);
      label.append(` ${item.nombre}`);
      container.appendChild(label);
      container.appendChild(document.createElement('br'));
    });
  }

  async function actualizarStaff() {
    const divVal = division.value;
    const ramaVal = rama.value;

    // Si no hay división o rama, mostrar "Seleccionar" dentro de cada contenedor
    if (!divVal || !ramaVal) {
        Object.values(contenedores).forEach(c => {
            if (c) c.innerHTML = '<span class="placeholder">Seleccionar</span>';
        });
        return;
    }

    const url = `/cargar_staff?division=${divVal}&rama=${ramaVal}`;
    try {
      const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const data = await res.json();
      if (!data.ok) return;

      fillCheckboxContainer(contenedores.entrenadores, data.entrenadores, 'entrenadores');
      fillCheckboxContainer(contenedores.ayudantes, data.ayudantes, 'ayudantes');
      fillCheckboxContainer(contenedores.pfs, data.pfs, 'pfs');
      fillCheckboxContainer(contenedores.managers, data.managers, 'managers');
    } catch (e) {
      console.error('Error cargando staff:', e);
    }
  }

  if (division) division.addEventListener('change', actualizarStaff);
  if (rama)     rama.addEventListener('change', actualizarStaff);
});
