// Al pulsar una miniatura, se muestra en el espacio de la foto principal
document.querySelectorAll("[data-galeria]").forEach((miniatura) => {
  miniatura.addEventListener("click", () => {
    const principal = document.getElementById("foto-principal");
    if (principal) {
      principal.src = miniatura.src;
    }
  });
});