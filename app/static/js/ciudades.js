document.addEventListener("DOMContentLoaded", () => {
  const provincia = document.getElementById("provincia_id");
  const ciudad = document.getElementById("ciudad_id");
  if (!provincia || !ciudad) return;

  provincia.addEventListener("change", async () => {
    ciudad.disabled = true;
    ciudad.innerHTML = '<option value="" disabled selected>Cargando...</option>';
    try {
      const respuesta = await fetch(`/admin/provincias/${provincia.value}/ciudades`);
      if (!respuesta.ok) throw new Error("Error al cargar");
      const ciudades = await respuesta.json();
      ciudad.innerHTML = '<option value="" disabled selected>Selecciona...</option>';
      for (const c of ciudades) {
        const opcion = document.createElement("option");
        opcion.value = c.id;
        opcion.textContent = c.nombre;
        ciudad.appendChild(opcion);
      }
    } catch {
      ciudad.innerHTML = '<option value="" disabled selected>No se pudo cargar</option>';
    } finally {
      ciudad.disabled = false;
    }
  });
});
