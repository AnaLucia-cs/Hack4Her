document.addEventListener("DOMContentLoaded", function () {

    // =====================
    // MAPA BASE
    // =====================
const mapa = L.map('mexico').setView([23.6345, -102.5528], 5);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
}).addTo(mapa);

setTimeout(() => {
    mapa.invalidateSize();
}, 200);

    // =====================
    // CENTROS DE ESTADOS
    // =====================
    const coordsEstados = {
        "Aguascalientes": [21.8853, -102.2916],
        "Baja California": [30.8406, -115.2838],
        "Baja California Sur": [26.0444, -111.6661],
        "Campeche": [19.8301, -90.5349],
        "Chiapas": [16.7569, -93.1292],
        "Chihuahua": [28.6320, -106.0691],
        "Ciudad de México": [19.4326, -99.1332],
        "Coahuila": [27.0587, -101.7068],
        "Colima": [19.1223, -104.0072],
        "Durango": [24.5593, -104.6588],
        "Guanajuato": [21.0190, -101.2574],
        "Guerrero": [17.4392, -99.5451],
        "Hidalgo": [20.0911, -98.7624],
        "Jalisco": [20.6597, -103.3496],
        "Estado de México": [19.2826, -99.6557],
        "Michoacán": [19.5665, -101.7068],
        "Morelos": [18.6813, -99.1013],
        "Nayarit": [21.7514, -104.8455],
        "Nuevo León": [25.5922, -99.9962],
        "Oaxaca": [17.0732, -96.7266],
        "Puebla": [19.0414, -98.2063],
        "Querétaro": [20.5888, -100.3899],
        "Quintana Roo": [19.1817, -88.4791],
        "San Luis Potosí": [22.1565, -100.9855],
        "Sinaloa": [25.1721, -107.4795],
        "Sonora": [29.2972, -110.3309],
        "Tabasco": [17.8409, -92.6189],
        "Tamaulipas": [23.7414, -99.1450],
        "Tlaxcala": [19.3139, -98.2404],
        "Veracruz": [19.1738, -96.1342],
        "Yucatán": [20.7099, -89.0943],
        "Zacatecas": [22.7709, -102.5832]
    };

    // =====================
    // COLORES NEGOCIO
    // =====================
    const coloresNegocio = {
        "panaderia": "#f97316",
        "abarrotes": "#3b82f6",
        "farmacia": "#10b981",
        "kiosco": "#ef4444",
        "licoreria": "#8b5cf6",
        "mayorista": "#06b6d4",
        "minisuper": "#84cc16",
        "tienda_organica": "#22c55e",
        "verduleria": "#65a30d",
        "hogares": "#f59e0b",
        "tienda_carne_pollo_pescado": "#dc2626"
    };

    // =====================
    // CLIENTES
    // =====================
    const clientes = [
        { estado: "Tamaulipas", tipo: "panaderia", riesgo: 0.9 },
        { estado: "Tamaulipas", tipo: "panaderia", riesgo: 0.9 },
        { estado: "Tamaulipas", tipo: "hogares", riesgo: 0.9 },
        { estado: "Nuevo León", tipo: "farmacia", riesgo: 0.6 },
        { estado: "Jalisco", tipo: "abarrotes", riesgo: 0.4 },
        { estado: "Puebla", tipo: "kiosco", riesgo: 0.8 },
        { estado: "Veracruz", tipo: "minisuper", riesgo: 0.7 }
    ];

    // =====================
    // RANDOM POINT
    // =====================
    function randomPointNear(lat, lng, spread = 0.6) {
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * spread;

        return [
            lat + Math.cos(angle) * radius,
            lng + Math.sin(angle) * radius
        ];
    }

    // =====================
    // PIN CLIENTES
    // =====================
    clientes.forEach(c => {

        const base = coordsEstados[c.estado];
        if (!base) return;

        const color = coloresNegocio[c.tipo] || "#000";
        const coords = randomPointNear(base[0], base[1], 0.6);

        const radius = c.riesgo > 0.8 ? 10 :
                       c.riesgo > 0.5 ? 7 : 5;

        L.circleMarker(coords, {
            radius: radius,
            color: color,
            fillColor: color,
            fillOpacity: 0.85,
            weight: 2
        })
        .addTo(mapa)
        .bindPopup(`
            <b>${c.tipo}</b><br>
            Estado: ${c.estado}<br>
            Riesgo: ${(c.riesgo * 100).toFixed(1)}%
        `);
    });

    // =====================
    // GEOJSON (SOLO BORDE NEGRO)
    // =====================
    fetch("https://raw.githubusercontent.com/angelnmara/geojson/refs/heads/master/mexicoHigh.json")
    .then(res => res.json())
    .then(data => {

        L.geoJSON(data, {

    style: function () {
        return {
            color: "#000000",
            weight: 0.8,        // 🔽 más delgado
            fill: false,
            opacity: 0.5        // 🔽 más suave (no compite con puntos)
        };
    },

    onEachFeature: function (feature, layer) {

        const name = feature.properties.name;

        layer.bindPopup(`<b>${name}</b>`);

        layer.on({
            mouseover: (e) => {
                e.target.setStyle({
                    weight: 1.5,     // leve resaltado
                    opacity: 0.8
                });
            },
            mouseout: (e) => {
                e.target.setStyle({
                    weight: 0.8,
                    opacity: 0.5
                });
            }
        });
    }

}).addTo(mapa);

    });

});