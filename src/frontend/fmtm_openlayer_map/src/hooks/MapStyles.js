import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import { Icon, Style,} from 'ol/style';
import React, { useEffect, useState } from 'react'
import CoreModules from 'fmtm/CoreModules';
import AssetModules from 'fmtm/AssetModules';
import {getCenter} from 'ol/extent';
import Point from 'ol/geom/Point.js';

function createPolygonStyle(fillColor, strokeColor) {
    return new Style({
        stroke: new Stroke({
            color: strokeColor,
            width: 3,
        }),
        fill: new Fill({
            color: fillColor,
        }),
    });
}
function createIconStyle(iconSrc) {
    return new Style({
        image: new Icon({
            anchor: [0.5, 1],
            scale:1.5,
            anchorXUnits: "fraction",
            anchorYUnits: "pixels",
            src: iconSrc,
        }),
        geometry: function (feature) {
            // return the coordinates of the centroid of the polygon
            const coordinates = feature.getGeometry().getExtent();
            const center = getCenter(coordinates);
            return new Point(center);
          },
    });
}
export default function MapStyles() {
    const mapTheme = CoreModules.useAppSelector(state => state.theme.hotTheme)
    const [style, setStyle] = useState({})
    const strokeColor= 'rgb(0,0,0,0.5)';

    useEffect(() => {
        
        
        
        // Example usage:
        const lockedPolygonStyle = createPolygonStyle(mapTheme.palette.mapFeatureColors.locked_for_mapping_rgb, strokeColor);
        const lockedValidationStyle = createPolygonStyle(mapTheme.palette.mapFeatureColors.locked_for_validation_rgb, strokeColor);
        const iconStyle = createIconStyle(AssetModules.LockPng);
        const redIconStyle = createIconStyle(AssetModules.RedLockPng);
       
        const geojsonStyles = {

            'READY': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.ready_rgb,
                }),
            }),
            'LOCKED_FOR_MAPPING': [lockedPolygonStyle, iconStyle],
            'MAPPED': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.mapped_rgb
                }),
            }),
            'LOCKED_FOR_VALIDATION': [lockedValidationStyle,redIconStyle],

            'VALIDATED': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.validated_rgb
                }),
            }),
            'INVALIDATED': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.invalidated_rgb
                }),
            }),
            'BAD': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.bad_rgb
                }),
            }),
            'SPLIT': new Style({
                stroke: new Stroke({
                color: strokeColor,
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.split_rgb
                }),
            }),
        };
        setStyle(geojsonStyles)
    }, [])

    return style;

}
