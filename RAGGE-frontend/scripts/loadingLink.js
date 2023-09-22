// Función para mostrar la pantalla de carga
function mostrarPantallaCarga(destino) {
    var pantallaCarga = document.getElementById("pantalla-carga");
    pantallaCarga.style.display = "flex";

    setTimeout(function() {
        // Redirigir al destino después de 2 segundos
        window.location.href = destino;
    }, 0); // 2000 milisegundos (2 segundos)
}


// Función para ocultar la pantalla de carga
function ocultarPantallaCarga() {
    var pantallaCarga = document.getElementById("pantalla-carga");
    pantallaCarga.style.display = "none";
}

// Agrega un evento de clic a todos los enlaces que muestre la pantalla de carga
var enlaces = document.querySelectorAll("a");

for (var i = 0; i < enlaces.length; i++) {
    enlaces[i].addEventListener("click", function(event) {
        event.preventDefault(); // Evita la navegación predeterminada
        var destino = this.getAttribute("href");
        mostrarPantallaCarga(destino);
    });
}

window.addEventListener("load", ocultarPantallaCarga);

