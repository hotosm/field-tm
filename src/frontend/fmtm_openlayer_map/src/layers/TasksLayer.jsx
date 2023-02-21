import { Vector as VectorLayer } from 'ol/layer.js';
import GeoJSON from 'ol/format/GeoJSON';
import { Vector as VectorSource } from 'ol/source.js';

import { useEffect } from 'react';
import { geojsonObjectModel } from '../models/geojsonObjectModel';
import MapStyles from '../hooks/MapStyles';
import { useSelector } from 'react-redux';

const TasksLayer = (map) => {
    const state = useSelector(state => state.project.projectData)
    // const demoState = useSelector(data=>data.maptasks)
    // console.log(demoState,'demo')
    const geojsonStyles = MapStyles();

    useEffect(() => {

        if (Object.keys(state).length != 0) {

            const styleFunction = function (feature) {
                let id = feature.getId();
                return geojsonStyles[id.split('_')[1]];
            };

            const geojsonObject = { ...geojsonObjectModel }

            state.project_tasks.forEach((task) => {
                geojsonObject['features'].push({
                    id: `${task.id}_${task.task_status_str}`,
                    type: task.outline_geojson.type,
                    geometry: task.outline_geojson.geometry,
                    properties: task.properties
                })
            })

            console.log('tasks :', geojsonObject)

            const vectorSource = new VectorSource({
                features: new GeoJSON().readFeatures(geojsonObject),
            });

            const vectorLayer = new VectorLayer({
                source: vectorSource,
                style: styleFunction,
            });
            map.addLayer(vectorLayer)
            map.getView().setZoom(13.5);
            map.getView().setCenter([
                36.43770834094465,
                -0.7831897260220853
            ])

        }

    }, [state])

}

export default TasksLayer;