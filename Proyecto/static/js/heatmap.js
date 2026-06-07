document.addEventListener("DOMContentLoaded", function () {

const riesgoEstados = {
    "Nuevo León": 0.85,
    "Jalisco": 0.62,
    "Ciudad de México": 0.30,
    "Puebla": 0.55,
    "Veracruz": 0.72
};

function getColor(value) {
    return value > 0.8 ? '#b91c1c' :
           value > 0.6 ? '#ef4444' :
           value > 0.4 ? '#f59e0b' :
           value > 0.2 ? '#facc15' :
                         '#22c55e';
}

// 🗺️ MAPA
const mapa = L.map('mexico').setView([23.6345, -102.5528], 5);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
}).addTo(mapa);

// 🧠 GEOJSON
fetch("https://raw.githubusercontent.com/angelnmara/geojson/refs/heads/master/mexicoHigh.json")
.then(res => res.json())
.then(data => {

    L.geoJSON(data, {

        style: function(feature) {

            const name = feature.properties.name;
            const value = riesgoEstados[name] || 0;

            return {
                fillColor: getColor(value),
                weight: 1,
                color: "#ffffff",
                fillOpacity: 0.75
            };
        },

        onEachFeature: function(feature, layer) {

            const name = feature.properties.name;
            const value = riesgoEstados[name] || 0;

            layer.bindPopup(`
                <b>${name}</b><br>
                Riesgo: ${(value * 100).toFixed(1)}%
            `);

            layer.on({
                mouseover: (e) => {
                    e.target.setStyle({
                        weight: 3,
                        color: "#111",
                        fillOpacity: 0.9
                    });
                },

                mouseout: (e) => {
                    e.target.setStyle({
                        weight: 1,
                        color: "#ffffff",
                        fillOpacity: 0.75
                    });
                }
            });
        }

    }).addTo(mapa);

});

});