/* eslint-disable no-console */
/* eslint-disable consistent-return */
import React, { useEffect, useRef, useState } from 'react';
import { get } from 'ol/proj';
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style.js';
import GeoJSON from 'ol/format/GeoJSON';
import { Vector as VectorSource } from 'ol/source';
import OLVectorLayer from 'ol/layer/Vector';
import { defaultStyles, getStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { isExtentValid } from '@/components/MapComponent/OpenLayersComponent/helpers/layerUtils';
import { Draw, Modify, Snap, Select, defaults as defaultInteractions } from 'ol/interaction.js';
import { getArea } from 'ol/sphere';
import { valid } from 'geojson-validation';
import Point from 'ol/geom/Point.js';
import MultiPoint from 'ol/geom/MultiPoint.js';
import { buffer } from 'ol/extent';
import { bbox as OLBbox } from 'ol/loadingstrategy';
import { geojson as FGBGeoJson } from 'flatgeobuf';

import { isValidUrl } from '@/utilfunctions/urlChecker';

const selectElement = 'singleselect';

const selectedCountry = new Style({
  stroke: new Stroke({
    color: '#008099',
    width: 3,
  }),
  // fill: new Fill({
  //   color: 'rgba(200,20,20,0.4)',
  // }),
});
let selection = {};
const layerViewProperties = {
  padding: [50, 50, 50, 50],
  duration: 900,
  constrainResolution: true,
};

const VectorLayer = ({
  map,
  geojson,
  fgbUrl,
  fgbExtent,
  style = { ...defaultStyles },
  zIndex = 0,
  zoomToLayer = false,
  visibleOnMap = true,
  properties,
  viewProperties = layerViewProperties,
  hoverEffect,
  mapOnClick = () => {},
  setStyle,
  onModify = null,
  onDraw,
  getTaskStatusStyle,
  layerProperties,
  rotation,
  getAOIArea,
  processGeojson,
}) => {
  const latestFgbRequestIdRef = useRef(0);
  const [vectorLayer, setVectorLayer] = useState(null);

  useEffect(() => {
    if (map && vectorLayer) {
      return () => map.removeLayer(vectorLayer);
    }
  }, [map, vectorLayer]);

  // Modify Feature
  useEffect(() => {
    if (!map) return;
    if (!vectorLayer) return;
    if (!onModify) return;
    const select = new Select({
      wrapX: false,
    });
    const vectorLayerSource = vectorLayer.getSource();
    const modify = new Modify({
      // features: select.getFeatures(),
      source: vectorLayerSource,
    });
    modify.on('modifyend', function (e) {
      var geoJSONFormat = new GeoJSON();

      var geoJSONString = geoJSONFormat.writeFeatures(vectorLayer.getSource().getFeatures(), {
        dataProjection: 'EPSG:4326',
        featureProjection: 'EPSG:3857',
      });
      const features = vectorLayer.getSource().getFeatures();
      const area = formatArea(features);

      onModify(geoJSONString, area);
    });
    map.addInteraction(modify);
    map.addInteraction(select);

    return () => {
      // map.removeInteraction(defaultInteractions().extend([select, modify]));
      map.removeInteraction(modify);
      map.removeInteraction(select);
    };
  }, [map, vectorLayer, onModify]);

  const formatArea = function (features) {
    const totalArea = features?.reduce((acc, curr) => acc + getArea(curr.getGeometry()), 0);
    let output;
    if (totalArea > 10000) {
      output = Math.round((totalArea / 1000000) * 100) / 100 + ' km\xB2';
    } else {
      output = Math.round(totalArea * 100) / 100 + ' m\xB2';
    }
    return output;
  };

  // Draw Feature
  useEffect(() => {
    if (!map) return;
    if (!onDraw) return;
    const source = new VectorSource({ wrapX: false });

    const vector = new OLVectorLayer({
      source: source,
    });

    const draw = new Draw({
      source: source,
      type: 'Polygon',
    });

    draw.on('drawend', function (e) {
      const feature = e.feature;
      const geojsonFormat = new GeoJSON();
      const newGeojson = geojsonFormat.writeFeature(feature, {
        dataProjection: 'EPSG:4326',
        featureProjection: 'EPSG:3857',
      });

      const geometry = feature.getGeometry();
      const area = formatArea([feature]);

      onDraw(newGeojson, area);
    });
    map.addInteraction(draw);
    return () => {
      map.removeInteraction(draw);
    };
  }, [map, vectorLayer, onDraw]);

  function fgbBoundingBox(originalExtent) {
    // Add a 50m buffer to the bbox search
    const bufferMeters = 50;
    const bufferedExtent = buffer(originalExtent, bufferMeters);

    const minPoint = new Point([bufferedExtent[0], bufferedExtent[1]]);
    minPoint.transform('EPSG:3857', 'EPSG:4326');

    const maxPoint = new Point([bufferedExtent[2], bufferedExtent[3]]);
    maxPoint.transform('EPSG:3857', 'EPSG:4326');

    return {
      minX: minPoint.getCoordinates()[0],
      minY: minPoint.getCoordinates()[1],
      maxX: maxPoint.getCoordinates()[0],
      maxY: maxPoint.getCoordinates()[1],
    };
  }

  function geomWithin(geom, area) {
    // Only include features that intersect extent
    let geomCoord;

    if (geom.getType() === 'Point') {
      geomCoord = geom.getCoordinates();
    } else if (geom.getType() === 'Polygon') {
      geomCoord = geom.getInteriorPoint().getCoordinates();
    } else if (geom.getType() === 'LineString') {
      geomCoord = geom.getExtent();
    }

    if (area.intersectsCoordinate(geomCoord)) {
      return true;
    }

    return false;
  }

  async function loadFgbRemote(filterExtent = true, extractGeomCol = true) {
    const fgbRequestIdRef = ++latestFgbRequestIdRef.current;
    this.clear();
    let filteredFeatures = [];
    for await (let feature of FGBGeoJson.deserialize(fgbUrl, fgbBoundingBox(fgbExtent.getExtent()))) {
      if (fgbRequestIdRef !== latestFgbRequestIdRef.current) return; // only process latest response

      if (extractGeomCol && feature.geometry.type === 'GeometryCollection') {
        // Extract first geom from geomcollection
        feature = {
          ...feature,
          geometry: feature.geometry.geometries[0],
        };
      }
      let extractGeom = new GeoJSON().readFeature(feature, {
        dataProjection: 'EPSG:4326',
        featureProjection: 'EPSG:3857',
      });

      // Clip geoms to another geometry (i.e. ST_Within)
      if (filterExtent) {
        if (geomWithin(extractGeom.getGeometry(), fgbExtent)) {
          filteredFeatures.push(extractGeom);
        }
      } else {
        filteredFeatures.push(extractGeom);
      }
    }
    // Process Geojson if needed i.e. filter, modify, etc
    // ex: in our use case we are filtering only rejected entities
    if (processGeojson) {
      filteredFeatures = processGeojson(filteredFeatures);
    }
    this.addFeatures(filteredFeatures);
  }

  function triggerMapClick(feature) {
    // Perform an action if a feature is found
    if (feature) {
      // Extract properties
      const properties = feature.getProperties();
      mapOnClick(properties, feature);
    }
  }

  useEffect(() => {
    if (!map) return;
    if (!geojson) return;
    if (!valid(geojson)) return;

    const geoJsonVectorLyr = new OLVectorLayer({
      source: new VectorSource({
        features: new GeoJSON().readFeatures(geojson, {
          featureProjection: get('EPSG:3857'),
        }),
      }),
      declutter: true,
    });

    const vlFeature = geoJsonVectorLyr?.getSource().getFeatures();
    if (!vlFeature || (vlFeature && vlFeature?.length === 0)) return;

    const handleClick = (evt) => {
      var pixel = evt.pixel;
      const feature = map.forEachFeatureAtPixel(pixel, function (feature, layer) {
        if (layer === geoJsonVectorLyr) {
          return feature;
        }
      });

      triggerMapClick(feature);
    };

    map.on('click', handleClick);

    setVectorLayer(geoJsonVectorLyr);
    return () => {
      setVectorLayer(null);
      map.un('click', handleClick);
    };
  }, [map, geojson]);

  useEffect(() => {
    if (!map || !fgbUrl || !isValidUrl(fgbUrl)) return;

    const fgbVectorLayer = new OLVectorLayer({
      source: new VectorSource({
        useSpatialIndex: true,
        strategy: OLBbox,
        loader: loadFgbRemote,
      }),
    });

    const handleClick = (evt) => {
      const pixel = evt.pixel;

      const feature = map.forEachFeatureAtPixel(pixel, function (feature, layer) {
        if (layer === fgbVectorLayer) {
          return feature;
        }
      });

      triggerMapClick(feature);
    };

    map.on('click', handleClick);

    setVectorLayer(fgbVectorLayer);

    return () => {
      setVectorLayer(null);
      map.un('click', handleClick);
    };
  }, [fgbUrl, fgbExtent]);

  useEffect(() => {
    if (!map || !vectorLayer) return;
    if (visibleOnMap) {
      map.addLayer(vectorLayer);
    } else {
      map.removeLayer(vectorLayer);
    }
  }, [map, vectorLayer, visibleOnMap]);

  useEffect(() => {
    if (!map || !vectorLayer || !visibleOnMap || !setStyle) return;
    vectorLayer.setStyle(setStyle);
  }, [map, setStyle, vectorLayer, visibleOnMap]);

  useEffect(() => {
    if (!map || !vectorLayer || !getTaskStatusStyle) return;
    vectorLayer.setStyle((feature) => getTaskStatusStyle(feature));
  }, [map, vectorLayer, getTaskStatusStyle]);

  useEffect(() => {
    if (!vectorLayer || !style.visibleOnMap || setStyle) return;
    vectorLayer.setStyle((feature, resolution) => {
      return onModify
        ? [
            new Style({
              image: new CircleStyle({
                radius: 5,
                fill: new Fill({
                  color: 'orange',
                }),
              }),
              geometry: function (feature) {
                // return the coordinates of the first ring of the polygon
                const coordinates = feature.getGeometry().getCoordinates()[0];
                return new MultiPoint(coordinates);
              },
            }),
            getStyles({ style, feature, resolution }),
          ]
        : [getStyles({ style, feature, resolution })];
    });
  }, [vectorLayer, style, setStyle, onModify]);

  useEffect(() => {
    if (vectorLayer) {
      vectorLayer.setZIndex(zIndex);
    }
  }, [vectorLayer, zIndex]);

  useEffect(() => {
    if (!map || !vectorLayer || !zoomToLayer) return;
    const source = vectorLayer.getSource();
    if (source.getFeatures().length === 0) return;
    const extent = source.getExtent();
    if (!isExtentValid(extent)) return;
    map.getView().fit(extent, viewProperties);
  }, [map, vectorLayer, zoomToLayer]);

  // set properties to features for identifying popup
  useEffect(() => {
    if (!vectorLayer || !properties) return;
    const features = vectorLayer.getSource().getFeatures();
    features.forEach((feat) => {
      feat.setProperties(properties);
    });
  }, [vectorLayer, properties]);

  useEffect(() => {
    if (!map || !vectorLayer || !layerProperties) return;
    vectorLayer.setProperties(layerProperties);
  }, [map, vectorLayer, layerProperties]);

  // style on hover
  useEffect(() => {
    if (!map || !vectorLayer || !hoverEffect) return;
    const selectionLayer = new OLVectorLayer({
      map,
      renderMode: 'vector',
      source: vectorLayer.getSource(),
      style: (feature) => {
        if (feature.getId() in selection) {
          return selectedCountry;
        }
      },
    });
    const pointerMovefn = (event) => {
      vectorLayer.getFeatures(event.pixel).then((features) => {
        if (!features.length) {
          selection = {};
          hoverEffect(undefined, vectorLayer);

          selectionLayer.changed();
          return;
        }
        const feature = features[0];
        if (!feature) {
          return;
        }
        const fid = feature.getId();
        if (selectElement.startsWith('singleselect')) {
          selection = {};
        }
        // add selected feature to lookup
        selection[fid] = feature;
        hoverEffect(selection[fid]);

        selectionLayer.changed();
      });
    };
    map.on('pointermove', pointerMovefn);
    return () => {
      map.un('pointermove', pointerMovefn);
    };
  }, [vectorLayer, hoverEffect]);

  // ROTATE ICON IMAGE ACCORDING TO ORIENTATION
  useEffect(() => {
    if (!map) return;
    if (typeof rotation === 'number') {
      // const mapRotation = map.getView().getRotation();
      setStyle?.getImage().setRotation(rotation);
    }
  }, [rotation, map, geojson]);

  useEffect(() => {
    if (!vectorLayer || !getAOIArea) return;
    const features = vectorLayer.getSource().getFeatures();
    const area = formatArea(features);
    getAOIArea(area);
  }, [vectorLayer, getAOIArea]);

  // ROTATE MAP ACCORDING TO ORIENTATION
  // useEffect(() => {
  //   if (!map) return;
  //   if (rotation) {
  //     map.getView().setRotation(rotation);
  //   }
  // }, [rotation, map]);
  return null;
};

export default VectorLayer;
