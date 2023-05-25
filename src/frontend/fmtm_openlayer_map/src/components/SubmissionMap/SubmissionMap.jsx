import React,{useState} from 'react';
import useOLMap from '../../hooks/useOlMap';
import { MapContainer as MapComponent } from '../MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../MapComponent/OpenLayersComponent/LayerSwitcher/index.js'
import { VectorLayer } from '../MapComponent/OpenLayersComponent/Layers';
import CoreModules from 'fmtm/CoreModules';

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
    const projectTaskBoundries = CoreModules.useSelector((state) => state.project.projectTaskBoundries);
    const projectBuildingGeojson = CoreModules.useSelector((state) => state.project.projectBuildingGeojson);
    const [projectBoundaries, setProjectBoundaries] = useState(null)
    const [buildingBoundaries, setBuildingBoundaries] = useState(null)
    const { mapRef, map } = useOLMap({
        // center: fromLonLat([85.3, 27.7]),
        center: [0, 0],
        zoom: 4,
        maxZoom: 25,
    });

    if(projectTaskBoundries?.length>0 && projectBoundaries === null){

        const taskGeojsonFeatureCollection = {
            ...basicGeojsonTemplate,
            features: [...projectTaskBoundries?.[0]?.taskBoundries?.map((task)=> ({...task.outline_geojson,id:task.outline_geojson.properties.uid}))]
    
        };
        setProjectBoundaries(taskGeojsonFeatureCollection)
    }
    if(projectBuildingGeojson?.length>0 && buildingBoundaries === null){
        
        const buildingGeojsonFeatureCollection = {
            ...basicGeojsonTemplate,
            features: projectBuildingGeojson.map((feature) => ({ ...feature.geometry, id: feature.id }))
            
        };
        setBuildingBoundaries(buildingGeojsonFeatureCollection);
    }

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
                {projectBoundaries?.type && <VectorLayer
                    geojson={projectBoundaries}
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
                    zIndex={5}
                />}
                {buildingBoundaries?.type && <VectorLayer
                    geojson={buildingBoundaries}
                    zIndex={10}
                />}
                {/* )} */}
            </MapComponent>
        </div>
    )
}

SubmissionMap.propTypes = {}

export default SubmissionMap