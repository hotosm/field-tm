import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import Style from 'ol/style/Style';
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux';

export default function MapStyles() {


    const mapTheme = useSelector(state => state.theme.hotTheme)
    const [style,setStyle] = useState({})

    useEffect(() => {

        const geojsonStyles = {

            'READY': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.ready,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.ready_rgb,
                }),
            }),
            'LOCKED_FOR_MAPPING': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.locked_for_mapping,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.locked_for_mapping_rgb
                }),
            }),
            'MAPPED': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.mapped,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.mapped_rgb
                }),
            }),
            'LOCKED_FOR_VALIDATION': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.locked_for_validation,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.locked_for_validation_rgb
                }),
            }),

            'VALIDATED': new Style({

                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.validated,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.validated_rgb
                }),
            }),
            'INVALIDATED': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.invalidated,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.invalidated_rgb
                }),
            }),
            'BAD': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.bad,
                    lineDash: [4],
                    width: 3,
                }),
                fill: new Fill({
                    color: mapTheme.palette.mapFeatureColors.bad_rgb
                }),
            }),
            'SPLIT': new Style({
                stroke: new Stroke({
                    color: mapTheme.palette.mapFeatureColors.split,
                    lineDash: [4],
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
