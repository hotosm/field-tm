/* eslint-disable no-console */
/* eslint-disable consistent-return */
/* eslint-disable react/forbid-prop-types */
import React,{ useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { get } from 'ol/proj';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import GeoJSON from 'ol/format/GeoJSON';
import { Vector as VectorSource } from 'ol/source';
import OLVectorLayer from 'ol/layer/Vector';
import { defaultStyles, getStyles } from '../helpers/styleUtils';
import { isExtentValid } from '../helpers/layerUtils';
import {
  Modify,
  Select,
  defaults as defaultInteractions,
} from 'ol/interaction.js';

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
  style,
  zIndex,
  zoomToLayer = false,
  visibleOnMap = true,
  properties,
  viewProperties,
  hoverEffect,
  mapOnClick,
  setStyle,
  onModify,
}) => {
  const [vectorLayer, setVectorLayer] = useState(null);

  useEffect(() => () => map && vectorLayer && map.removeLayer(vectorLayer), [map, vectorLayer]);

  // Modify Feature
  useEffect(() => {
    if(!map) return;
    if(!vectorLayer) return;
    if(!onModify) return;
    const select = new Select({
      wrapX: false,
    });
    const vectorLayerSource = vectorLayer.getSource();
    const modify = new Modify({
      // features: select.getFeatures(),
      source:vectorLayerSource
    });
    modify.on('modifyend',function(e){
      var geoJSONFormat = new GeoJSON();

      // Step 3: Convert features to GeoJSON
      var geoJSONString = geoJSONFormat.writeFeatures(vectorLayer.getSource().getFeatures(),{ dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});

      // Step 4: Log the GeoJSON string
      console.log(geoJSONString,'geojsonString');
      onModify(geoJSONString);
      // console.log(JSON.stringify(geoJSONString),'geojsonString Stringify');
    });
    map.addInteraction(modify);
    map.addInteraction(select);

    // map.addInteraction(defaultInteractions().extend([select, modify]));
    return () => {
      // map.removeInteraction(defaultInteractions().extend([select, modify]))
    }
  }, [map,vectorLayer,onModify])
  useEffect(() => {
    if (!map) return;

    const vectorLyr = new OLVectorLayer({
      source: new VectorSource({
        features: new GeoJSON().readFeatures(geojson, {
          featureProjection: get('EPSG:3857'),
        }),
      }),
      declutter: true,
    });
    map.on('click', (evt) => {
      var pixel = evt.pixel;
      const feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
       
        if (layer === vectorLyr) {  
          return feature;
        }
      });
      
      // Perform an action if a feature is found
      if (feature) {
        // Do something with the feature
        console.log('Clicked feature:', feature.getProperties());
        // dispatch()
        mapOnClick(feature.getProperties());
      }
    });
    setVectorLayer(vectorLyr);
  }, [map, geojson]);

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
    if (!vectorLayer || !style.visibleOnMap) return;
    vectorLayer.setStyle((feature, resolution) => getStyles({ style, feature, resolution }));
  }, [vectorLayer, style]);

  useEffect(() => {
    if (!vectorLayer) return;
    vectorLayer.setZIndex(zIndex);
  }, [vectorLayer, zIndex]);

  useEffect(() => {
    if (!map || !vectorLayer || !zoomToLayer) return;
    const extent = vectorLayer.getSource().getExtent();
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

  

// style on hover
useEffect(() => {
  if (!map) return null;
  if (!vectorLayer) return null;
  if (!hoverEffect) return null;
  const selectionLayer = new OLVectorLayer({
    map,
    renderMode: 'vector',
    source: vectorLayer.getSource(),
    // eslint-disable-next-line consistent-return
    style: (feature) => {
      if (feature.getId() in selection) {
        return selectedCountry;
      }
      // return stylex;
    },
  });
  function pointerMovefn(event) {
    vectorLayer.getFeatures(event.pixel).then((features) => {
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
}, [vectorLayer]);
  return null;
};





VectorLayer.defaultProps = {
  zIndex: 0,
  style: { ...defaultStyles },
  zoomToLayer: false,
  viewProperties: layerViewProperties,
  mapOnClick:()=>{},
  onModify:null,
};

VectorLayer.propTypes = {
  geojson: PropTypes.object.isRequired,
  style: PropTypes.object,
  zIndex: PropTypes.number,
  zoomToLayer: PropTypes.bool,
  viewProperties: PropTypes.object,
  mapOnClick:PropTypes.func,
  onModify:PropTypes.func,
  // Context: PropTypes.object.isRequired,
};

export default VectorLayer;
