import { useEffect, useState } from 'react';
import AnimatedCluster from 'ol-ext/layer/AnimatedCluster';
import * as olExtent from 'ol/extent';
import GeoJSON from 'ol/format/GeoJSON';
import Stroke from 'ol/style/Stroke';
import Style from 'ol/style/Style';
import Fill from 'ol/style/Fill';
import { Cluster, OSM as OSMSource } from 'ol/source';
import { Text, Circle, Icon } from 'ol/style';
import VectorSource from 'ol/source/Vector';
import { hexToRgba } from '../../../MapComponent/OpenLayersComponent/helpers/styleUtils';
import SelectCluster from 'ol-ext/interaction/SelectCluster';
import MarkerIcon from '../../../../assets/images/red_marker.png';

function setAsyncStyle(style, feature, getIndividualStyle) {
  const styleCache = {};
  const size = feature?.get('features')?.length;
  let stylex = styleCache[size];
  if (size === 1) {
    const featureProperty = feature?.get('features')[0].getProperties();
    stylex = getIndividualStyle(featureProperty);
    styleCache[size] = stylex;
    return stylex;
  } else {
    stylex = new Style({
      image: new Circle({
        radius: 23,
        stroke: new Stroke({
          color: hexToRgba(style.color, style.opacity || 100),
          width: 6,
        }),
        fill: new Fill({
          color: hexToRgba(style.background_color, style.opacity || 100),
          width: 40,
        }),
      }),
      text: new Text({
        text: size.toString(),
        fill: new Fill({
          color: '#fff',
        }),
        font: '16px Arial',
      }),
    });
    styleCache[size] = stylex;
    return stylex;
  }
}

const ClusterLayer = ({
  map,
  source: layerSource,
  zIndex = 999,
  zoomToLayer = true,
  visibleOnMap = true,
  style,
  mapOnClick,
  getIndividualStyle,
}) => {
  const [vectorLayer, setVectorLayer] = useState(null);
  useEffect(() => () => map && vectorLayer && map.removeLayer(vectorLayer), [map, vectorLayer]);

  useEffect(() => {
    if (!map || !layerSource || !layerSource.features) return;
    const sourceOSM = new OSMSource();
    const vectorSource = new VectorSource({
      features: new GeoJSON().readFeatures(layerSource, {
        defaultDataProjection: 'EPSG:3857',
        featureProjection: sourceOSM.getProjection(),
      }),
    });

    const clusterSource = new Cluster({
      distance: parseInt(50, 10),
      source: vectorSource,
    });

    const animatedClusterLayer = new AnimatedCluster({
      source: clusterSource,
      animationDuration: 700,
      distance: 40,
      style: (feature) => setAsyncStyle(style, feature, getIndividualStyle),
    });

    setVectorLayer(animatedClusterLayer);
  }, [map, layerSource]);

  useEffect(() => {
    if (map && vectorLayer) {
      vectorLayer.setZIndex(zIndex);
    }
  }, [map, vectorLayer, zIndex]);

  useEffect(() => {
    if (map && vectorLayer && zoomToLayer) {
      setTimeout(() => {
        const features = vectorLayer.getSource().getFeatures();
        const extent = olExtent.createEmpty();
        features.forEach((feat) =>
          feat.values_?.features.forEach((feature) => olExtent.extend(extent, feature.getGeometry().getExtent())),
        );
        map.getView().fit(extent, {
          padding: [50, 50, 50, 50],
        });
      }, 300);
    }
  }, [map, vectorLayer, zoomToLayer]);

  useEffect(() => {
    if (!map) return;
    map.on('singleclick', (evt) => {
      let area_no_9_extent = null;
      map.forEachFeatureAtPixel(
        evt.pixel,
        (featurex) => {
          area_no_9_extent = featurex.getGeometry().getExtent();
          return featurex;
        },
        true,
      );
      if (area_no_9_extent) {
        map.getView().fit(area_no_9_extent, {
          duration: 1000,
          padding: [50, 50, 50, 50],
          // maxZoom: 11,
        });
      }
    });

    return () => {
      map.un('singleclick', () => {});
    };
  }, [map]);

  useEffect(() => {
    if (!map) return;

    map.on('singleclick', (evt) => {
      const features = map.getFeaturesAtPixel(evt.pixel);
      if (features.length > 0) {
        const featureProperties = features[0].getProperties();
        const feature = featureProperties.features[0].getProperties();
        if (featureProperties.features.length === 1) {
          mapOnClick(feature);
        } else {
          return;
        }
      }
    });

    return () => {
      map.un('singleclick', () => {});
    };
  }, [map]);

  useEffect(() => {
    if (!map || !vectorLayer) return;
    if (visibleOnMap) {
      map.addLayer(vectorLayer);
    } else {
      map.removeLayer(vectorLayer);
    }
  }, [map, vectorLayer, visibleOnMap]);

  useEffect(() => () => map && map.removeLayer(vectorLayer), [map, vectorLayer]);

  useEffect(() => {
    if (!map) return;
    // Select interaction to spread cluster out and select features
    const selectCluster = new SelectCluster({
      selectCluster: false, // disable cluster selection
      circleMaxObjects: 20,
      pointRadius: 40,
      spiral: true,
      animate: true,
      autoClose: true,
      // Feature style when springs apart
      featureStyle: clusterSingleFeatureStyle,
    });
    map.addInteraction(selectCluster);

    function clusterSingleFeatureStyle(clusterMember) {
      // Call for expandedFeatures pass a resolution instead
      const isExpandedFeature = clusterMember.get('selectclusterfeature');

      if (isExpandedFeature) {
        const feature = clusterMember.getProperties().features[0];
        const featureProperty = feature?.getProperties();
        console.log(featureProperty, 'featureProperty');
        console.log(feature, 'isExpandedFeature');
        const style = new Style({
          image: new Icon({
            src: MarkerIcon,
            scale: 0.06,
          }),
          text: new Text({
            text: featureProperty?.project_id,
            fill: new Fill({
              color: 'black',
            }),
            offsetY: 25,
            font: '15px Times New Roman',
          }),
        });
        return style;
        fillColor = '#96bfff';
      } else {
        return;
      }
    }

    return () => {
      map.removeInteraction(selectCluster);
    };
  }, [map]);

  return null;
};

export default ClusterLayer;
