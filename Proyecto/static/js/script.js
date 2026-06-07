document.addEventListener("DOMContentLoaded", function () {

// =====================
// MAPA BASE
// =====================
const mapa = L.map('mexico').setView([23.6345, -102.5528], 5);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
}).addTo(mapa);

// =====================
// COORDENADAS CENTRO ESTADOS
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
// COLORES POR NEGOCIO
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
    "hogares":"f59e0b",
    "tienda_carne_pollo_pescado":"dc2626"

};

// =====================
// FUNCION RANDOM DENTRO DEL ESTADO
// =====================
function randomPointNear(lat, lng, spread = 0.4) {
    const latOffset = (Math.random() - 0.5) * spread;
    const lngOffset = (Math.random() - 0.5) * spread;

    return [lat + latOffset, lng + lngOffset];
}

// =====================
// DATOS EJEMPLO (puedes cambiarlo por Flask luego)
// =====================
const clientes = [
    { estado: "Tamaulipas", tipo: "panaderia", riesgo: 0.9, cantidad: 12 },
    { estado: "Nuevo León", tipo: "farmacia", riesgo: 0.6, cantidad: 8 },
    { estado: "Jalisco", tipo: "abarrotes", riesgo: 0.4, cantidad: 10 },
    { estado: "Puebla", tipo: "kiosco", riesgo: 0.8, cantidad: 6 },
    { estado: "Veracruz", tipo: "minisuper", riesgo: 0.7, cantidad: 7 }
];

// =====================
// CREAR PUNTOS EN MAPA
// =====================
clientes.forEach(c => {

    const base = coordsEstados[c.estado];
    if (!base) return;

    const color = coloresNegocio[c.tipo] || "#000";

    for (let i = 0; i < c.cantidad; i++) {

        const coords = randomPointNear(base[0], base[1], 0.5);

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
    }
});

});