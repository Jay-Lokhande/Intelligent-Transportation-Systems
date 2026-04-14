/**
 * Initial map view: URL ?lat=&lon=&zoom= overrides localStorage "itsViewerMapStart"
 * JSON { "lat", "lon", "zoom" }, then built-in default (Bengaluru bbox center).
 */
(function () {
  const DEF = { lat: 12.955, lon: 77.64, zoom: 12 };
  const STORAGE_KEY = "itsViewerMapStart";

  function parseNum(v) {
    if (v == null || v === "") return null;
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : null;
  }

  window.itsViewerGetMapStart = function getMapStart() {
    let o = { ...DEF };
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const j = JSON.parse(raw);
        if (typeof j.lat === "number" && typeof j.lon === "number") {
          o.lat = j.lat;
          o.lon = j.lon;
          if (typeof j.zoom === "number" && j.zoom >= 1 && j.zoom <= 19) o.zoom = j.zoom;
        }
      }
    } catch (e) {
      /* ignore */
    }
    const u = new URLSearchParams(window.location.search);
    const qlat = parseNum(u.get("lat"));
    const qlon = parseNum(u.get("lon"));
    const qzoom = parseNum(u.get("zoom"));
    if (qlat != null) o.lat = qlat;
    if (qlon != null) o.lon = qlon;
    if (qzoom != null) o.zoom = Math.max(1, Math.min(19, qzoom));
    return o;
  };

  window.itsViewerSaveMapStart = function saveMapStart(lat, lon, zoom) {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          lat: Number(lat),
          lon: Number(lon),
          zoom: Math.max(1, Math.min(19, Number(zoom))),
        })
      );
    } catch (e) {
      /* ignore */
    }
  };

  window.itsViewerApplyQueryToUrl = function applyQueryToUrl(lat, lon, zoom) {
    try {
      const u = new URL(window.location.href);
      u.searchParams.set("lat", String(lat));
      u.searchParams.set("lon", String(lon));
      u.searchParams.set("zoom", String(zoom));
      window.history.replaceState({}, "", u.toString());
    } catch (e) {
      /* file:// etc. */
    }
  };
})();
