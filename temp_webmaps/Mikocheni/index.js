const map = L.map("map").setView([-6.785568, 39.261278], 13);
const osm = L.tileLayer(
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }
).addTo(map);

//creating some icons

var houseIcon = L.icon({
  iconUrl: 'data/download.svg',
  iconSize:     [20, 52], // size of the icon
  iconAnchor:   [22, 94], // point of the icon which will correspond to marker's location
  popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});

//L.marker([-6.785568, 39.261278], {icon: houseIcon}).addTo(map);


fetch("data/Mikocheni.geojson")
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      L.geoJSON(data).addTo(map);
    })

fetch("data/Mikocheni_dumb_grid.geojson")
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      L.geoJSON(data).addTo(map).bindPopup("<img src=data/QR_codes/Mikocheni_buildings_197.gif>");
    })


   
   /* function onEachFeature(feature, layer) {
      layer.bindPopup(feature.properties.name);
    }
    fetch("data/Mikocheni_grid_centroids.geojson")
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      L.geoJSON(data, {
        pointToLayer: function (feature, latlng) {
                  return L.marker(latlng, {icon: houseIcon});
          },
        onEachFeature: onEachFeature
      }).addTo(map);
  
    })
*/
    
    