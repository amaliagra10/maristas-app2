document.addEventListener("DOMContentLoaded", function () {

    const btn = document.getElementById("btn-checkin");
    if (!btn) return;

    btn.addEventListener("click", function () {

        console.log("CLICK detectado");

        const actividad_id = this.dataset.actividad; // lo dejamos por si luego lo usás
        const csrfToken = this.dataset.csrf;

        if (!navigator.geolocation) {
            alert("Tu navegador no soporta geolocalización.");
            return;
        }

        navigator.geolocation.getCurrentPosition(

            function (position) {

                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                fetch(`/actividad/${actividad_id}/presencialidad-entrenadores/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: new URLSearchParams({
                        lat: lat,
                        lon: lon
                    })
                })

                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Error en la respuesta del servidor");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.success) {
                        alert(data.success);
                        location.reload();
                    } else if (data.error) {
                        alert(data.error);
                    } else {
                        alert("Respuesta inesperada del servidor.");
                    }
                })
                .catch(function (error) {
                    console.error(error);
                    alert("No se pudo registrar la presencialidad.");
                });
            },

            function (error) {
                console.error(error);
                alert("Necesitamos tu ubicación para registrar la presencialidad.");
            }

        );

    });

});
