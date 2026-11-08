/* 地图页：Leaflet + 高德瓦片，点击标记弹出相册封面并跳转照片墙。
   站点开启了 navigation.instant（无刷新跳转），因此用 document$.subscribe
   在每次页面切换后重新初始化；地图瓦片与 Leaflet 库都走 CDN，无需申请 Key。
   注意：高德底图使用 GCJ-02 坐标系，而相册点位是 WGS-84 经纬度，直接叠加会偏移
   几百米，因此加载时统一把 WGS-84 转成 GCJ-02 再放置标记。 */
document$.subscribe(function () {
  var el = document.getElementById("gallery-map");
  if (!el || typeof L === "undefined") return;
  // 防止 instant 导航回到本页时重复初始化
  if (el.dataset.inited) return;
  el.dataset.inited = "1";

  var map = L.map(el, { scrollWheelZoom: true });

  // 高德街道瓦片（GCJ-02 坐标系）；加载失败时自动回退 OSM（WGS-84）
  var usingAmap = true;
  var amapLayer = L.tileLayer(
    "https://webrat0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
    {
      subdomains: ["1", "2", "3", "4"],
      maxZoom: 18,
      attribution: '&copy; <a href="https://lbs.amap.com/">高德地图</a>',
    }
  );
  var osmLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> 贡献者',
  });
  amapLayer.addTo(map);

  var tileErrors = 0;
  var markerGroup = L.layerGroup().addTo(map);
  amapLayer.on("tileerror", function () {
    // 个别瓦片失败属正常（缩放边缘等），连续失败才判定底图不可用
    if (!usingAmap) return;
    if (++tileErrors >= 8) {
      usingAmap = false;
      map.removeLayer(amapLayer);
      osmLayer.addTo(map);
      renderMarkers(); // OSM 是 WGS-84，需用原始坐标重建标记
    }
  });

  // ---- WGS-84 -> GCJ-02（高德底图对齐用，标准换算法则，无需依赖库）----
  var PI = 3.1415926535897932384626;
  var A = 6378245.0;
  var EE = 0.00669342162296594323;
  function outOfChina(lng, lat) {
    return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271;
  }
  function tLat(x, y) {
    var r = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
    r += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    r += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
    r += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
    return r;
  }
  function tLng(x, y) {
    var r = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
    r += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    r += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
    r += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
    return r;
  }
  function wgs2gcj(lng, lat) {
    if (outOfChina(lng, lat)) return [lng, lat];
    var dLat = tLat(lng - 105.0, lat - 35.0);
    var dLng = tLng(lng - 105.0, lat - 35.0);
    var radLat = lat / 180.0 * PI;
    var magic = Math.sin(radLat);
    magic = 1 - EE * magic * magic;
    var sqrtMagic = Math.sqrt(magic);
    dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI);
    dLng = (dLng * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI);
    return [lng + dLng, lat + dLat];
  }

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

  // 根据当前底图渲染标记：高德用 GCJ-02，OSM 用原始 WGS-84
  function renderMarkers() {
    markerGroup.clearLayers();
    var bounds = [];
    points.forEach(function (p) {
      if (!p.lat || !p.lng) return;
      var pos = usingAmap ? (function () { var g = wgs2gcj(p.lng, p.lat); return [g[1], g[0]]; })()
                          : [p.lat, p.lng];
      var marker = L.marker(pos).addTo(markerGroup);
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
      bounds.push(pos);
    });
    if (bounds.length) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
    }
  }

  renderMarkers();
});
