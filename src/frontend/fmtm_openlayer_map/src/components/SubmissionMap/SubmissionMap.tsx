import React, { useEffect } from 'react';
import useOLMap from '../../hooks/useOlMap';
import { MapContainer as MapComponent } from '../MapComponent/OpenLayersComponent';
import { fromLonLat } from 'ol/proj';
import LayerSwitcherControl from '../MapComponent/OpenLayersComponent/LayerSwitcher/index.js'
import CoreModules from 'fmtm/CoreModules';
import { VectorLayer } from '../MapComponent/OpenLayersComponent/Layers';

function elastic(t) {
    return (
        Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1
    );
}
const basicGeojsonTemplate = {
    "type": "FeatureCollection",
    "features": []
};
const SubmissionMap = () => {
    const projectState = CoreModules.useSelector((state) => state.project);
    const params = CoreModules.useParams();

    const { mapRef, map } = useOLMap({
        // center: fromLonLat([85.3, 27.7]),
        center: [0, 0],
        zoom: 4,
        maxZoom: 25,
    });

    const taskGeojsonFeatureCollection = {
        ...basicGeojsonTemplate,
        features: [{ ...projectState?.projectTaskBoundries[projectState?.projectTaskBoundries.length - 1].taskBoundries?.[0]?.outline_geojson, id: projectState?.projectTaskBoundries[projectState?.projectTaskBoundries.length - 1].taskBoundries?.[0]?.outline_geojson?.properties.uid }]

        // features: projectState?.projectTaskBoundries?.map((task) => {
        //     return { ...task.taskBoundries?.[0]?.outline_geojson, id: task.taskBoundries?.[0]?.outline_geojson?.properties.uid }
        // })
    };
    console.log(taskGeojsonFeatureCollection);

    return (
        <div className="map-container" style={{ height: '100%' }}>
            <MapComponent
                ref={mapRef}
                mapInstance={map}
                className="map naxatw-relative naxatw-min-h-full naxatw-w-full"
                style={{
                    height: '100%',
                    width: '100%',
                }}
            >
                <LayerSwitcherControl />
                {/* <div className="naxatw-map-tools naxatw-absolute naxatw-m-1  naxatw-rounded-lg naxatw-z-[1]">
                <MapToolBar map={map} />
                </div> */}
                {/* {coordinates.latitude && coordinates.longitude && ( */}
                <VectorLayer
                    geojson={taskGeojsonFeatureCollection}
                    // stylestyle={{
                    //     ...getStyles,
                    //     fillOpacity: 100,
                    //     lineColor: getStyles.fillColor,
                    //     lineThickness: 7,
                    //     lineOpacity: 40,
                    // }}
                    viewProperties={{
                        // easing: elastic,
                        // animate: true,
                        size: map?.getSize(),
                        // maxZoom: 15,
                        padding: [50, 50, 50, 50],
                        // duration: 900,
                        constrainResolution: true,
                        duration: 2000,
                    }}
                    zoomToLayer
                />
                {/* )} */}
            </MapComponent>
        </div>
    )
}

SubmissionMap.propTypes = {}

export default SubmissionMap