import React, { useState } from 'react';
import useOLMap from '../hooks/useOlMap';
import { MapContainer as MapComponent } from '../components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js'
import { VectorLayer } from '../components/MapComponent/OpenLayersComponent/Layers';
// import { VectorLayer } from '../MapComponent/OpenLayersComponent/Layers';

function elastic(t) {
    return (
        Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1
    );
}
const basicGeojsonTemplate = {
    "type": "FeatureCollection",
    "features": []
};
const DefineAreaMap = ({uploadedGeojson}) => {
    const [convertedJSON, setConvertedJSON] = useState(null)
    // const projectTaskBoundries = CoreModules.useSelector((state) => state.project.projectTaskBoundries);
    // const projectBuildingGeojson = CoreModules.useSelector((state) => state.project.projectBuildingGeojson);

    const { mapRef, map } = useOLMap({
        // center: fromLonLat([85.3, 27.7]),
        center: [0, 0],
        zoom: 4,
        maxZoom: 25,
    });
    console.log(uploadedGeojson,'uploadedGeojson');
    // const formattedGeojson = 
    if(uploadedGeojson){

        const fileReader = new FileReader();
        fileReader.readAsText(uploadedGeojson, "UTF-8");
        fileReader.onload = e => {
        //   console.log("e.target.result", e.target.result);
          setConvertedJSON(e.target.result);
        };
    }
    return (
        <div className="map-container" style={{ height: '100%',width:'100%' }}>
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
                {convertedJSON && <VectorLayer
                    geojson={convertedJSON}
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
                />}
            </MapComponent>
        </div>
    )
}

DefineAreaMap.propTypes = {}

export default DefineAreaMap