
import React, { useEffect, useRef, useState } from "react";
import Map from 'ol/Map'
import View from 'ol/View'
import { useDispatch, useSelector } from "react-redux";
import { Tile as TileLayer } from 'ol/layer.js';
import { OSM } from 'ol/source.js';
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import TasksLayer from "../layers/TasksLayer";
import environment from "fmtm/environment";
import BasicDialog from 'fmtm/BasicDialog';
import DialogActions from "../components/DialogActions";
import { MapTasksActions } from "../store/slices/MapTasksSlice";
import { ProjectActions } from "../store/slices/ProjectSlice";


export default function MainView() {
  const stateDialog = useSelector(state=>state.project.dialogStatus)
 
  const dispatch = useDispatch();

  const [taskId, setTaskId] = useState()
  const mapElement = useRef();
  const [map, setMap] = useState()

  const [featuresLayer, setFeaturesLayer] = useState()

  useEffect(() => {

    const initalFeaturesLayer = new VectorLayer({
      source: new VectorSource()
    })

    const initialMap = new Map({
      target: mapElement.current,
      layers: [
        new TileLayer({
          source: new OSM(),
          visible: true
        }),
        initalFeaturesLayer
      ],
      view: new View({
        projection: 'EPSG:4326',
        center: [0, 0],
        zoom: 3,
      })
    })

    initialMap.on('click', function (event) {

      initialMap.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
        if ( environment.tasksStatus.indexOf(feature.getId().split('_')[1])!= -1 ) {
          setFeaturesLayer(feature)
          setTaskId(feature.getId().split('_')[0])
          dispatch(ProjectActions.SetDialogStatus(true))
        }
      });
    });

    setMap(initialMap)
    setFeaturesLayer(initalFeaturesLayer)

  }, [])


  TasksLayer(map)

  return (
    <div ref={mapElement} id="map_container" >
      <BasicDialog open={stateDialog}
        onClose={() => {
          dispatch(ProjectActions.SetDialogStatus(false))
        }}
        title={`#${taskId}`}
        iconCloseMode={true}
        element={<DialogActions feature={featuresLayer} taskId={taskId}  />}
      />
    </div>
  )
}