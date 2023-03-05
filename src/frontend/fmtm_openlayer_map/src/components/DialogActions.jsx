import { Button, Stack } from '@mui/material'
import React from 'react'
import environment from "fmtm/environment";
import { useDispatch, useSelector } from 'react-redux';
import ProjectTaskStatus from '../api/ProjectTaskStatus';
import MapStyles from '../hooks/MapStyles';
import { ProjectActions } from '../store/slices/ProjectSlice';
import { useParams } from 'react-router-dom';

export default function Dialog({ taskId, feature, map, view }) {
    const featureStatus = feature.id_ != undefined ? feature.id_.replace("_", ",").split(',')[1] : null;
    const projectData = useSelector(state => state.project.projectTaskBoundries)
    const geojsonStyles = MapStyles()
    const dispatch = useDispatch();
    const params = useParams();
    const currentProjectId = environment.decode(params.id)

    const index = environment.tasksStatus.findIndex(data => data.key == featureStatus)
    const tasksStatusList = feature.id_ != undefined ? environment.tasksStatus[index]['value'] : []
    const tasksList = environment.tasksStatus.map((status) => {
        return status.key
    })

    const handleOnClick = (event) => {

        const status = event.target.id;
        const body = {
            username: 'mohamed',
            id: 1
        }
        const geoStyle = geojsonStyles[status];
        dispatch(ProjectActions.SetDialogStatus(false))
        dispatch(
            ProjectTaskStatus(`${environment.baseApiUrl}/tasks/${taskId}/new_status/${status}`,
                geoStyle, projectData, currentProjectId, feature, map, view, taskId, body)
        )
    }

    return (
        <Stack direction={'column'} p={3} spacing={2}>
            {
                tasksList.map((data, index) => {
                    return (
                        tasksStatusList.indexOf(data) != -1 ?
                            <Button
                                id={data}
                                key={index}
                                variant="contained"
                                color='error'
                                onClick={handleOnClick}
                                disabled={false}
                            >
                                {data.replaceAll('_', ' ')}
                            </Button> :
                            <Button
                                id={data}
                                key={index}
                                variant="contained"
                                color='error'
                                onClick={handleOnClick}
                                disabled={true}
                            >
                                {data.replaceAll('_', ' ')}
                            </Button>
                    )
                })
            }
        </Stack>
    )
}
