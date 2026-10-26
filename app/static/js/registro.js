document.addEventListener("DOMContentLoaded", () => {
  const provincia = document.getElementById("provincia_id");
  const ciudad = document.getElementById("ciudad_id");
  const cedula = document.getElementById("cedula");
  const formulario = document.querySelector('form[action="/registro"]');
  if (provincia && ciudad) {
    provincia.addEventListener("change", async () => {
      ciudad.disabled = true;
      ciudad.innerHTML = '<option value="" disabled selected>Cargando...</option>';
      try {
        const respuesta = await fetch(`/registro/provincias/${provincia.value}/ciudades`);
        if (!respuesta.ok) throw new Error("No se pudieron cargar las ciudades");
        const ciudades = await respuesta.json();
        ciudad.innerHTML = '<option value="" disabled selected>Selecciona...</option>';
        for (const item of ciudades) {
          const opcion = document.createElement("option");
          opcion.value = item.id;
          opcion.textContent = item.nombre;
          ciudad.appendChild(opcion);
        }
      } catch {
        ciudad.innerHTML = '<option value="" disabled selected>No se pudieron cargar las ciudades</option>';
      } finally {
        ciudad.disabled = false;
      }
    });
  }

  const cedulaValida = (valor) => {
    const numero = valor.replace(/[\s-]/g, "");
    if (!/^\d{10}$/.test(numero)) return false;
    const provinciaCodigo = Number(numero.slice(0, 2));
    if (provinciaCodigo < 1 || provinciaCodigo > 24 || Number(numero[2]) > 5) return false;
    let suma = 0;
    for (let i = 0; i < 9; i += 1) {
      let digito = Number(numero[i]);
      if (i % 2 === 0) {
        digito *= 2;
        if (digito > 9) digito -= 9;
      }
      suma += digito;
    }
    return (10 - (suma % 10)) % 10 === Number(numero[9]);
  };

  if (cedula) {
    cedula.addEventListener("input", () => {
      cedula.setCustomValidity(cedulaValida(cedula.value) ? "" : "Ingresa una cédula ecuatoriana válida.");
    });
  }
  if (formulario) {
    formulario.addEventListener("submit", (evento) => {
      const password = formulario.elements.password;
      const password2 = formulario.elements.password2;
      password2.setCustomValidity(password.value === password2.value ? "" : "Las contraseñas no coinciden.");
      if (cedula) cedula.setCustomValidity(cedulaValida(cedula.value) ? "" : "Ingresa una cédula ecuatoriana válida.");
      if (!formulario.reportValidity()) evento.preventDefault();
    });
  }
});
