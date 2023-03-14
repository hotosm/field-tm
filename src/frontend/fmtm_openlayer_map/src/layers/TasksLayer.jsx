import { Vector as VectorLayer } from 'ol/layer.js';
import GeoJSON from 'ol/format/GeoJSON';
import { Vector as VectorSource } from 'ol/source.js';
import { easeOut } from 'ol/easing';
import { useEffect } from 'react';
import { geojsonObjectModel } from '../models/geojsonObjectModel';
import MapStyles from '../hooks/MapStyles';
import environment from "fmtm/environment";
import CoreModules from 'fmtm/CoreModules';

const TasksLayer = (map, view, feature) => {
    const params = CoreModules.useParams();
    const state = CoreModules.useSelector(state => state.project)
    const geojsonStyles = MapStyles(feature);

    useEffect(() => {

        if (state.projectTaskBoundries.length != 0 && map != undefined) {

            if (state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id)) != -1) {

                const index = state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id));

                const styleFunction = function (feature) {
                    let id = feature.getId().toString().replace("_", ",");
                    geojsonStyles[id.split(',')[1]]
                    return geojsonStyles[id.split(',')[1]];
                };

                const geojsonObject = { ...geojsonObjectModel }

                state.projectTaskBoundries[index].taskBoundries.forEach((task) => {
                    geojsonObject['features'].push({
                        id: `${task.id}_${task.task_status_str}`,
                        type: task.outline_geojson.type,
                        geometry: task.outline_geojson.geometry,
                        // properties: task.properties
                    })
                })

                const vectorSource = new VectorSource({
                    features: new GeoJSON().readFeatures(geojsonObject),

                });

                const vectorLayer = new VectorLayer({
                    source: vectorSource,
                    style: styleFunction,
                });

                const centroid = state.projectTaskBoundries[index].
                    taskBoundries[state.projectTaskBoundries[index].
                        taskBoundries.length - 1].
                    outline_centroid.geometry.coordinates;

                map.getView().setCenter(centroid)

                setTimeout(() => {
                    view.animate({ zoom: 15, easing: easeOut, duration: 2000, });
                }, 500);

                map.addLayer(vectorLayer)
                map.on('loadend', function () {
                    map.getTargetElement().classList.remove('spinner');
                });
            }
        }

    }, [state.newProjectTrigger, map])

    // useEffect(() => {

    //     if (state.projectTaskBoundries.length != 0 && map != undefined) {
    //         if (state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id)) != -1) {
    //         }
    //     }
    // }, [map])




}

export default TasksLayer;
