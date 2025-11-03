import React, { useEffect } from 'react';
import SearchNominatim from 'ol-ext/control/SearchNominatim';
import '@/components/MapComponent/OpenLayersComponent/map.css';
import 'ol-ext/dist/ol-ext.css';
import GeoJSON from 'ol/format/GeoJSON';

const Search = ({ map }) => {
  useEffect(() => {
    if (!map) return;

    const search = new SearchNominatim({
      reverse: false,
      position: true,
      zoomOnSelect: true,
      maxItems: 10,
    });

    map.addControl(search);

    search.on('select', function (e) {
      if (e.search?.geometry || e.search?.geojson) {
        const format = new GeoJSON();
        const feature = format.readFeature(e.search.geojson || e.search, {
          dataProjection: 'EPSG:4326',
          featureProjection: map.getView().getProjection(),
        });

        const extent = feature.getGeometry().getExtent();
        map.getView().fit(extent, { maxZoom: 16, duration: 1000 });
      } else if (e.coordinate) {
        map.getView().animate({ center: e.coordinate, zoom: 14, duration: 800 });
      }
    });

    return () => {
      map.removeControl(search);
    };
  }, [map]);

  return null;
};

export default Search;
