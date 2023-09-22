import { Stroke, Style } from 'ol/style';

const basicGeojsonTemplate = {
  type: 'FeatureCollection',
  features: [],
};

const buildingStyle = new Style({
  stroke: new Stroke({
    color: '#FF0000',
  }),
});

export { basicGeojsonTemplate, buildingStyle };
