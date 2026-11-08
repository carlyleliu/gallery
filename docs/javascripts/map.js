/* 地图页：Leaflet + OSM，点击标记弹出相册封面并跳转照片墙。
   站点开启了 navigation.instant（无刷新跳转），因此用 document$.subscribe
   在每次页面切换后重新初始化；地图瓦片与 Leaflet 库都走 CDN，无需申请 Key。 */
document$.subscribe(function () {
  var el = document.getElementById("gallery-map");
  if (!el || typeof L === "undefined") return;
  // 防止 instant 导航回到本页时重复初始化
  if (el.dataset.inited) return;
  el.dataset.inited = "1";

  var map = L.map(el, { scrollWheelZoom: true });

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> 贡献者',
  }).addTo(map);

  // 数据由内嵌的 <script id="map-data" type="application/json"> 提供
  var dataEl = document.getElementById("map-data");
  var points = [];
  try {
    points = JSON.parse(dataEl.textContent || "[]");
  } catch (e) {
    points = [];
  }
  if (!points.length) {
    map.setView([35.0, 105.0], 4);
    return;
  }

  var bounds = [];
  points.forEach(function (p) {
    if (!p.lat || !p.lng) return;
    var marker = L.marker([p.lat, p.lng]).addTo(map);
    var cover = p.cover
      ? '<a href="' + p.url + '"><img src="' + p.cover + '" alt="' + p.name +
        '" style="width:180px;height:auto;display:block;margin-bottom:6px;"></a>'
      : "";
    marker.bindPopup(
      '<div style="text-align:center">' + cover +
        '<a href="' + p.url + '" style="font-weight:600">' + p.name + "</a>" +
        (p.location ? '<div style="color:#888;font-size:.8em">' + p.location + "</div>" : "") +
        "</div>"
    );
    bounds.push([p.lat, p.lng]);
  });

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
  }
});
