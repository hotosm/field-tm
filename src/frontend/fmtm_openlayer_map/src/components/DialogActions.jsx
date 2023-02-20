import { Button, Stack } from '@mui/material'
import React from 'react'
import environment from "fmtm/environment";
import { useDispatch, useSelector } from 'react-redux';
import ProjectTaskStatus from '../api/ProjectTaskStatus';
import MapStyles from '../hooks/MapStyles';
import { ProjectActions } from '../store/slices/ProjectSlice';

export default function Dialog({ taskId, feature }) {
    const projectData = useSelector(state => state.project.projectData)
    const geojsonStyles = MapStyles()
    const dispatch = useDispatch();

    const tasksStatus = ['READY', 'LOCKED FOR MAPPING', 'LOCKED FOR VALIDATION',
        'VALIDATE', 'INVALIDATED', 'BAD', 'SPLIT', 'ARCHIVED']

    const handleOnClick = (event) => {
        const value = event.target.id;
        const status = value.replaceAll(' ', '_')
        const body = {
            username: 'mohamed',
            id: 1
        }
        const geoStyle = geojsonStyles[status];
        dispatch(ProjectActions.SetDialogStatus(false))
        dispatch(
            ProjectTaskStatus(`${environment.baseApiUrl}/tasks/${taskId}/new_status/${status}`,
                geoStyle, projectData, feature, body)
        )

    }

    return (
        <Stack direction={'column'} spacing={2}>
            {
                tasksStatus.map((data, index) => {
                    return (
                        <Button
                            id={data}
                            key={index}
                            variant="contained"
                            color='error'
                            onClick={handleOnClick}
                            disabled={false}
                        >
                            {data}
                        </Button>
                    )
                })
            }
        </Stack>
    )
}
