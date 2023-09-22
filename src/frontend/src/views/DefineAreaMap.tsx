import React, { useEffect, useState } from 'react';
import useOLMap from '../hooks/useOlMap';
import { MapContainer as MapComponent } from '../components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '../components/MapComponent/OpenLayersComponent/Layers';
import CoreModules from '../shared/CoreModules';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';

const DefineAreaMap = ({
  uploadedGeojson,
  setGeojsonFile,
  uploadedDataExtractFile,
  uploadedLineExtractFile,
  onDraw,
}) => {
  const drawnGeojson = CoreModules.useAppSelector((state) => state.createproject.drawnGeojson);
  const drawToggle = CoreModules.useAppSelector((state) => state.createproject.drawToggle);
  const dispatch = CoreModules.useAppDispatch();
  const [dataExtractedGeojson, setDataExtractedGeojson] = useState(null);
  const [lineExtractedGeojson, setLineExtractedGeojson] = useState(null);
  const dividedTaskGeojson = CoreModules.useAppSelector((state) => state.createproject.dividedTaskGeojson);

  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });

  useEffect(() => {
    if (dividedTaskGeojson) {
    } else if (uploadedGeojson) {
      const fileReader = new FileReader();
      fileReader.readAsText(uploadedGeojson, 'UTF-8');
      fileReader.onload = (e) => {
        dispatch(CreateProjectActions.SetDividedTaskGeojson(e.target.result));
      };
    } else {
      dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
    }
  }, [uploadedGeojson]);
  useEffect(() => {
    if (uploadedDataExtractFile) {
      const fileReader = new FileReader();
      fileReader.readAsText(uploadedDataExtractFile, 'UTF-8');
      fileReader.onload = (e) => {
        setDataExtractedGeojson(e.target.result);
      };
    } else {
      setDataExtractedGeojson(null);
    }
  }, [uploadedDataExtractFile]);
  useEffect(() => {
    if (uploadedLineExtractFile) {
      const fileReader = new FileReader();
      fileReader.readAsText(uploadedLineExtractFile, 'UTF-8');
      fileReader.onload = (e) => {
        setLineExtractedGeojson(e.target.result);
      };
    } else {
      setLineExtractedGeojson(null);
    }
  }, [uploadedLineExtractFile]);
  return (
    <div className="map-container" style={{ height: '600px', width: '100%' }}>
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
        {drawToggle && (
          <VectorLayer
            geojson={drawnGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            onDraw={onDraw}
            zoomToLayer
          />
        )}
        {dividedTaskGeojson && (
          <VectorLayer
            geojson={dividedTaskGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            // onModify={(modifiedGeojson) => {
            //   console.log(JSON.parse(modifiedGeojson));
            //   const parsedJSON = JSON.parse(modifiedGeojson)
            //   var f = new File([modifiedGeojson], "AOI.geojson", { type: "application/geo+json" })
            //   setGeojsonFile(f);
            // }}
            zoomToLayer
          />
        )}
        {dataExtractedGeojson && (
          <VectorLayer
            geojson={dataExtractedGeojson}
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
        )}
        {lineExtractedGeojson && (
          <VectorLayer
            geojson={lineExtractedGeojson}
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
        )}
      </MapComponent>
    </div>
  );
};

export default DefineAreaMap;
