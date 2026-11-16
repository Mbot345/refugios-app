document.addEventListener("DOMContentLoaded", () => {
  const rol = document.getElementById("rol");
  const contenedor = document.getElementById("fundacion-wrapper");
  if (!rol || !contenedor) return;

  const rolesFundacion = (rol.dataset.rolesFundacion || "").split(",");

  const actualizar = () => {
    contenedor.hidden = !rolesFundacion.includes(rol.value);
  };

  rol.addEventListener("change", actualizar);
  actualizar();
});