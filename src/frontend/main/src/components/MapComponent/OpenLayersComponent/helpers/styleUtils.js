import { Fill, Stroke, Style, Icon, Circle, Text } from 'ol/style';

export function hexToRgba(hex, opacity = 100) {
  if (!hex) return '';
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);
  const a = opacity * 0.01;
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

export function getPropertiesField(geojson) {
  return Object.keys(geojson.features[0].properties);
}

export function getGeometryType(geojson) {
  return geojson.features[0]?.geometry?.type;
}

// https://stackoverflow.com/questions/1152024/best-way-to-generate-a-random-color-in-javascript/1152508
export function getRandomColor() {
  return `#${`000000${Math.floor(Math.random() * 16777216).toString(16)}`.substr(-6)}`;
}

export const defaultStyles = {
  lineColor: '#000000',
  lineOpacity: 70,
  fillColor: '#1a2fa2',
  fillOpacity: 50,
  lineThickness: 1,
  circleRadius: 3,
  dashline: 0,
  showLabel: false,
  customLabelText: null,
  labelField: '',
  labelFont: 'Calibri',
  labelFontSize: 14,
  labelColor: '#000000',
  labelOpacity: 100,
  labelOutlineWidth: 3,
  labelOutlineColor: '#ffffff',
  labelOffsetX: 0,
  labelOffsetY: 0,
  labelText: 'normal',
  labelMaxResolution: 400,
  labelAlign: 'center',
  labelBaseline: 'middle',
  labelRotationDegree: 0,
  labelFontWeight: 'normal',
  labelPlacement: 'point',
  labelMaxAngleDegree: 45.0,
  labelOverflow: false,
  labelLineHeight: 1,
  visibleOnMap: true,
  icon: {},
  showSublayer: false,
  sublayerColumnName: '',
  sublayer: {},
};

export const municipalStyles = {
  ...defaultStyles,
  fillOpacity: 0,
  lineColor: '#ffffff',
};

export const defaultRasterStyles = {
  opacity: 100,
};

export const sublayerKeysException = ['showSublayer', 'sublayerColumnName', 'sublayer'];

function createIconMarker(style) {
  const {
    icon: { url, scale },
  } = style;
  // fetch(url)
  //   .then(res => res.blob())
  return new Icon({
    // anchor: [0.5, 46],
    // anchorXUnits: 'fraction',
    // anchorYUnits: 'pixels',
    scale: scale || 0.9,
    crossOrigin: 'anonymous',
    // imgSize: [1500, 1500],
    src: url,
  });
}

function createCircleMarker(style) {
  const { lineColor, lineOpacity, fillColor, fillOpacity, lineThickness, circleRadius } = style;
  return new Circle({
    radius: circleRadius,
    stroke: new Stroke({
      color: hexToRgba(lineColor, lineOpacity),
      width: lineThickness,
    }),
    fill: new Fill({
      color: hexToRgba(fillColor, fillOpacity),
    }),
  });
}

function stringDivider(str, width, spaceReplacer) {
  if (str.length > width) {
    let p = width;
    while (p > 0 && str[p] !== ' ' && str[p] !== '-') {
      p -= 1;
    }
    if (p > 0) {
      let left;
      if (str.substring(p, p + 1) === '-') {
        left = str.substring(0, p + 1);
      } else {
        left = str.substring(0, p);
      }
      const right = str.substring(p + 1);
      return left + spaceReplacer + stringDivider(right, width, spaceReplacer);
    }
  }
  return str;
}

function truncString(str, n) {
  return str.length > n ? `${str.substr(0, n - 1)}...` : str.substr(0);
}

function getText(style, feature, resolution) {
  const type = style.labelText;
  const maxResolution = style.labelMaxResolution;
  let text = style.showLabel ? style.customLabelText || feature.get(style.labelField)?.toString() || '' : '';

  if (resolution > maxResolution) {
    text = '';
  } else if (type === 'hide') {
    text = '';
  } else if (type === 'shorten') {
    text = truncString(text, 12);
  } else if (type === 'wrap' && (!style.labelPlacement || style.labelPlacement !== 'line')) {
    text = stringDivider(text, 16, '\n');
  }

  return text;
}

function createTextStyle(style, feature, resolution) {
  const {
    labelFont,
    labelFontSize,
    labelColor,
    labelOpacity,
    labelOutlineWidth,
    labelOutlineColor,
    labelOffsetX,
    labelOffsetY,
    labelAlign,
    labelBaseline,
    labelFontWeight,
    labelLineHeight,
    labelPlacement,
    labelMaxAngleDegree,
    labelRotationDegree,
  } = style;
  const font = labelFont
    ? `${labelFontWeight} ${labelFontSize}px/${labelLineHeight || 1} ${labelFont}`
    : '14px Calibri';
  return new Text({
    text: getText(style, feature, resolution),
    font,
    overflow: true,
    fill: new Fill({
      color: hexToRgba(labelColor, labelOpacity),
    }),
    stroke: new Stroke({
      color: hexToRgba(labelOutlineColor, labelOpacity),
      width: parseInt(labelOutlineWidth, 10),
    }),
    offsetX: labelOffsetX,
    offsetY: labelOffsetY,
    textAlign: labelAlign || undefined,
    textBaseline: labelBaseline,
    placement: labelPlacement,
    maxAngle: labelMaxAngleDegree,
    rotation: parseFloat(labelRotationDegree) || 0,
  });
}

export function generateLayerStylePoint(style, feature, resolution) {
  const { icon } = style;
  return new Style({
    image: icon?.url ? createIconMarker(style) : createCircleMarker(style),
    text: createTextStyle(style, feature, resolution),
  });
}

export function generateLayerStylePolygon(style, feature, resolution) {
  const { lineColor, lineOpacity, fillColor, fillOpacity, lineThickness, dashline } = style;
  return new Style({
    stroke: new Stroke({
      color: hexToRgba(lineColor, lineOpacity),
      width: lineThickness,
      lineDash: [dashline],
    }),
    fill: new Fill({
      color: hexToRgba(fillColor, fillOpacity),
    }),
    text: createTextStyle(style, feature, resolution),
  });
}

export function generateLayerStyleLine(style, feature, resolution) {
  return new Style({
    stroke: new Stroke({
      color: hexToRgba(style.lineColor, style.lineOpacity),
      width: style.lineThickness,
    }),
    fill: new Fill({
      color: hexToRgba(style.fillColor, style.fillOpacity),
    }),
    text: createTextStyle(style, feature, resolution),
  });
}

export function getStyles({ style, feature, resolution }) {
  const geometryType = feature.getGeometry().getType();
  switch (geometryType) {
    case 'Point':
      return generateLayerStylePoint(style, feature, resolution);
    case 'Polygon':
      return generateLayerStylePolygon(style, feature, resolution);
    case 'LineString':
      return generateLayerStyleLine(style, feature, resolution);
    case 'MultiLineString':
      return generateLayerStyleLine(style, feature, resolution);

    default:
      return generateLayerStylePolygon(style, feature, resolution);
  }
}
