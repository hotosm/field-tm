# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#

"""HTMX map helper utilities."""

import json
import time


def render_leaflet_map(
    map_id: str,
    geojson_layers: list[dict],
    height: str = "500px",
    show_controls: bool = True,
) -> str:
    """Render a Leaflet map with one or more GeoJSON layers.

    Args:
        map_id: Unique ID for the map container div
        geojson_layers: List of dicts with keys:
            - 'data': GeoJSON FeatureCollection dict
            - 'name': Display name for the layer
            - 'color': Hex color for the layer (default: '#3388ff')
            - 'weight': Line weight (default: 2)
            - 'opacity': Line opacity (default: 0.8)
            - 'fillOpacity': Fill opacity (default: 0.3)
        height: Height of the map container
        show_controls: Whether to show layer control (if multiple layers)

    Returns:
        HTML string with Leaflet map including CSS and JS
    """
    # Generate unique map ID to avoid conflicts with previous maps
    unique_map_id = f"{map_id}-{int(time.time() * 1000)}"

    # Escape GeoJSON for JavaScript
    escaped_layers = []
    for layer in geojson_layers:
        geojson_escaped = json.dumps(layer["data"]).replace("</script>", "<\\/script>")
        layer_config = {
            "data": geojson_escaped,
            "name": layer.get("name", "Layer"),
            "color": layer.get("color", "#3388ff"),
            "weight": layer.get("weight", 2),
            "opacity": layer.get("opacity", 0.8),
            "fillOpacity": layer.get("fillOpacity", 0.3),
        }
        escaped_layers.append(layer_config)

    layers_json = json.dumps(escaped_layers).replace("</script>", "<\\/script>")

    div_style = (  # noqa: E501
        f"height: {height}; width: 100%;"
        " border: 1px solid #ddd;"
        " border-radius: 4px; margin-bottom: 15px;"
    )
    tile_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    map_html = f"""
    <div id="{unique_map_id}" style="{div_style}"></div>
    <script>
        (function() {{
            var baseMapId = '{map_id}';
            var sel = '[id^="' + baseMapId + '-"]';
            var ecs = document.querySelectorAll(sel);
            ecs.forEach(function(container) {{
                if (container._leaflet_id
                    && typeof L !== 'undefined') {{
                    try {{
                        var om = L.Map.prototype.get(
                            container._leaflet_id);
                        if (om) {{ om.remove(); }}
                    }} catch (e) {{
                    }}
                }}
            }});

            function initMap() {{
                var mc = document.getElementById(
                    '{unique_map_id}');
                if (!mc) {{
                    setTimeout(initMap, 50);
                    return;
                }}

                if (typeof L === 'undefined') {{
                    var cssQ = 'link[href*="leaflet.css"]';
                    if (!document.querySelector(cssQ)) {{
                        var link = document.createElement(
                            'link');
                        link.rel = 'stylesheet';
                        link.href =
                            'https://unpkg.com/leaflet'
                            + '@1.9.4/dist/leaflet.css';
                        document.head.appendChild(link);
                    }}
                    var jsQ = 'script[src*="leaflet.js"]';
                    if (!document.querySelector(jsQ)) {{
                        var s = document.createElement(
                            'script');
                        s.src =
                            'https://unpkg.com/leaflet'
                            + '@1.9.4/dist/leaflet.js';
                        s.onload = function() {{
                            setTimeout(initMap, 100);
                        }};
                        document.head.appendChild(s);
                        return;
                    }}
                    setTimeout(initMap, 100);
                    return;
                }}

                if (mc._leaflet_id) {{
                    try {{
                        var em = L.Map.prototype.get(
                            mc._leaflet_id);
                        if (em) {{ em.remove(); }}
                    }} catch (e) {{
                    }}
                }}

                setTimeout(function() {{
                    try {{
                        var map = L.map(
                            '{unique_map_id}'
                        ).setView([0, 0], 2);

                        L.tileLayer(
                            '{tile_url}', {{
                            attribution:
                                '© OSM contributors',
                            maxZoom: 19
                        }}).addTo(map);

                        var lc = {layers_json};
                        var layers = [];
                        var allBounds = [];

                        lc.forEach(function(cfg, i) {{
                            var gd = JSON.parse(cfg.data);
                            var gl = L.geoJSON(gd, {{
                                style: function(f) {{
                                    return {{
                                        color: cfg.color,
                                        weight: cfg.weight,
                                        opacity: cfg.opacity,
                                        fillOpacity:
                                            cfg.fillOpacity
                                    }};
                                }},
                                onEachFeature:
                                  function(f, layer) {{
                                    if (f.properties) {{
                                        var ks = Object.keys(
                                            f.properties
                                        ).slice(0, 5);
                                        var ps = ks.map(
                                            function(k) {{
                                            return '<b>'
                                                + k
                                                + ':</b> '
                                                + f.properties[k];
                                        }}).join('<br>');
                                        var h = '<b>'
                                            + cfg.name
                                            + '</b><br>'
                                            + (ps || 'None');
                                        layer.bindPopup(h);
                                    }}
                                }}
                            }});

                            gl.addTo(map);
                            layers.push({{
                                name: cfg.name,
                                layer: gl
                            }});

                            if (gl.getBounds().isValid())
                                allBounds.push(
                                    gl.getBounds());
                        }});

                        var sc = {str(show_controls).lower()};
                        if (layers.length > 1 && sc) {{
                            var ctrl = L.control.layers(
                                {{}}, {{}});
                            layers.forEach(function(l) {{
                                ctrl.addOverlay(
                                    l.layer, l.name);
                            }});
                            ctrl.addTo(map);
                        }}

                        if (allBounds.length > 0) {{
                            var cb = allBounds[0];
                            for (var i = 1;
                                 i < allBounds.length;
                                 i++) {{
                                cb = cb.extend(
                                    allBounds[i]);
                            }}
                            map.fitBounds(cb);
                        }}

                        setTimeout(function() {{
                            map.invalidateSize();
                        }}, 100);
                    }} catch (error) {{
                        console.error(
                            'Map init error:', error);
                    }}
                }}, 100);
            }}

            if (document.getElementById(
                    '{unique_map_id}')) {{
                initMap();
            }} else {{
                var ias = function(event) {{
                    if (document.getElementById(
                            '{unique_map_id}')) {{
                        initMap();
                        document.body
                            .removeEventListener(
                            'htmx:afterSwap', ias);
                    }}
                }};
                document.body.addEventListener(
                    'htmx:afterSwap', ias);
            }}
        }})();
    </script>
    """
    return map_html
