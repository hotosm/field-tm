import React,{ useEffect, useMemo } from 'react';
// import * as olExtent from 'ol/extent';
import VectorTile from 'ol/layer/VectorTile';
import MVT from 'ol/format/MVT';
import VectorTileSource from 'ol/source/VectorTile';
import { transformExtent } from 'ol/proj';
import Stroke from 'ol/style/Stroke';
import Style from 'ol/style/Style';
import { getStyles, defaultStyles } from '../helpers/styleUtils';
import { isExtentValid } from '../helpers/layerUtils';

const selectElement = 'singleselect';

const selectedCountry = new Style({
  stroke: new Stroke({
    color: 'rgba(255,255,255,0.8)',
    width: 3,
  }),
  // fill: new Fill({
  //   color: 'rgba(200,20,20,0.4)',
  // }),
});
let selection = {};
const VectorTileLayer = ({
  map,
  url,
  style = { ...defaultStyles },
  zIndex = 1,
  visibleOnMap = true,
  authToken,
  setStyle,
  zoomToLayer = false,
  bbox = null,
  hoverEffect,
  // properties,
}) => {
  const vectorTileLayer = useMemo(
    () =>
      new VectorTile({
        renderMode: 'hybrid',
        // declutter: true,
      }),
    [],
  );

  vectorTileLayer.setProperties({ name: 'site' });

  // add source to layer
  useEffect(() => {
    if (!map) return;

    const requestHeader = new Headers();
    if (authToken) {
      requestHeader.append('Authorization', `Token ${authToken}`);
    }

    const vectorTileSource = new VectorTileSource({
      // format: new MVT({ featureClass: Feature }),
      format: new MVT({ idProperty: 'id' }),
      maxZoom: 19,
      url,
      transition: 0,

      tileLoadFunction: (tile, vtUrl) => {
        tile.setLoader((extent, resolution, projection) => {
          fetch(vtUrl, {
            headers: requestHeader,
          }).then((response) => {
            response.arrayBuffer().then((data) => {
              const format = tile.getFormat();
              const features = format.readFeatures(data, {
                extent,
                featureProjection: projection,
              });
              tile.setFeatures(features);
            });
          });
        });
      },
    });
    vectorTileLayer.setSource(vectorTileSource);
  }, [map, url, authToken, vectorTileLayer]);

  // add layer to map
  useEffect(() => {
    if (!map) return;
    if (visibleOnMap) {
      map.addLayer(vectorTileLayer);
    } else {
      map.removeLayer(vectorTileLayer);
    }
  }, [map, visibleOnMap, vectorTileLayer]);

  // // set style
  useEffect(() => {
    if (!map || !visibleOnMap || !setStyle) return;
    vectorTileLayer.setStyle(setStyle);
  }, [map, setStyle, vectorTileLayer, visibleOnMap]);

  // set style
  useEffect(() => {
    if (!map || !visibleOnMap || setStyle) return;
    vectorTileLayer.setStyle((feature, resolution) => getStyles({ style, feature, resolution }));
  }, [map, style, vectorTileLayer, visibleOnMap, setStyle]);

  // set z-index
  useEffect(() => {
    if (!map) return;
    vectorTileLayer.setZIndex(zIndex);
  }, [map, zIndex, vectorTileLayer]);

  // // set properties to features for identifying popup
  // useEffect(() => {
  //   if (!vectorTileLayer || !properties) return;
  //   vectorTileLayer.getSource().on('tileloadend', (evt) => {
  //     // const z = evt.tile.getTileCoord()[0];
  //     const features = evt.tile.getFeatures();
  //     features.forEach((feat) => {
  //       feat.setProperties(properties);
  //     });
  //   });
  //   // // console.log(vectorTileLayer.getSource(), 'sourcex');
  //   // const features = vectorTileLayer.getSource().getFeatures();
  //   // features.forEach((feat) => {
  //   //   feat.setProperties(properties);
  //   // });
  // }, [vectorTileLayer, properties]);

  // useEffect(() => {
  //   const featuresForZ = [];
  //   vectorTileLayer.getSource().on('tileloadend', evt => {
  //     const z = evt.tile.getTileCoord()[0];
  //     const feature = evt.tile.getFeatures();
  //     if (!Array.isArray(featuresForZ[z])) {
  //       featuresForZ[z] = [];
  //     }
  //     featuresForZ[z] = featuresForZ[z].concat(feature);
  //   });
  //   setFeatures(featuresForZ);
  // }, []);

  // useEffect(() => {
  //   if (!map) return;
  //   const extent = olExtent.createEmpty();
  //   if (isExtentValid(extent)) {
  //     map.getView().fit(extent, {
  //       padding: [50, 50, 50, 50],
  //       duration: 500,
  //       constrainResolution: true,
  //     });
  //   }
  // }, [map]);

  // style on hover
  useEffect(() => {
    if (!map) return null;
    if (!hoverEffect) return null;
    const selectionLayer = new VectorTile({
      map,
      renderMode: 'vector',
      source: vectorTileLayer.getSource(),
      // eslint-disable-next-line consistent-return
      style: (feature) => {
        if (feature.getId() in selection) {
          return selectedCountry;
        }
        // return stylex;
      },
    });
    function pointerMovefn(event) {
      vectorTileLayer.getFeatures(event.pixel).then((features) => {
        if (!features.length) {
          selection = {};
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

        selectionLayer.changed();
      });
    }
    map.on('pointermove', pointerMovefn);
    return () => {
      map.un('pointermove', pointerMovefn);
    };
  }, [vectorTileLayer]);

  // zoom to layer
  useEffect(() => {
    if (!map || !vectorTileLayer || !zoomToLayer || !bbox) return;
    const transformedExtent = transformExtent(bbox, 'EPSG:4326', 'EPSG:3857');
    if (!isExtentValid(transformedExtent)) return;
    map.getView().fit(transformedExtent, {
      padding: [50, 50, 50, 50],
      duration: 900,
      constrainResolution: true,
    });
  }, [map, vectorTileLayer, zoomToLayer, bbox]);

  // cleanup
  useEffect(() => () => map && map.removeLayer(vectorTileLayer), [map, vectorTileLayer]);

  return null;
};

export default VectorTileLayer;
