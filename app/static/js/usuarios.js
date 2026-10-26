document.addEventListener("DOMContentLoaded", () => {
  const rol = document.getElementById("rol");
  const contenedor = document.getElementById("fundacion-wrapper");
  if (!rol || !contenedor) return;
  const actualizar = () => { contenedor.hidden = rol.value !== "trabajador"; };
  rol.addEventListener("change", actualizar);
  actualizar();
});
