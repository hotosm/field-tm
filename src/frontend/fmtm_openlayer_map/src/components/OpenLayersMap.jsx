import { IconButton, Stack } from "@mui/material";
import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import IconButtonCard from "../utilities/IconButtonCard";
import BasicDialog from "../utilities/BasicDialog";
import DialogActions from "../components/DialogActions";
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import GridViewIcon from '@mui/icons-material/GridView';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import '../styles/home.scss'
import { ProjectActions } from "../store/slices/ProjectSlice";



const OpenLayersMap = (
    {
        defaultTheme,
        stateDialog,
        params,
        state,
        taskId,
        top,
        map,
        mainView,
        featuresLayer,
        mapElement,
        environment
    }) => {

    function elastic(t) {
        return (
            Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1
        );
    }
    const dispatch = useDispatch();
    const [fullView, setFullView] = useState(false)
    return (
        <Stack spacing={1} direction={'column'}>
            <Stack
                style={{ border: `4px solid ${defaultTheme.palette.error.main}`, }}
                justifyContent={'center'}
                height={608}

            >
                <div ref={mapElement} id="map_container" >

                    <BasicDialog
                        open={stateDialog}
                        title={`#${taskId}`}
                        onClose={() => {
                            dispatch(ProjectActions.SetDialogStatus(false))
                        }}
                        actions={<DialogActions map={map} view={mainView} feature={featuresLayer} taskId={taskId}
                        />}
                    />

                    <Stack
                        p={1}
                        // style={{ backgroundColor: 'rgb(0, 128, 153,0.1)' }}
                        className="fullview"
                        justifyContent={'center'}
                        spacing={3}
                        zIndex={1}
                        top={top}
                    >
                        <IconButtonCard
                            style={{ backgroundColor: 'white', right: 0 }}
                            element={
                                <IconButton onClick={() => {
                                    let actualZoom = map.getView().getZoom();
                                    map.getView().setZoom(actualZoom + 1)
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <AddIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{ backgroundColor: 'white', right: 0 }}
                            element={
                                <IconButton onClick={() => {
                                    let actualZoom = map.getView().getZoom();
                                    map.getView().setZoom(actualZoom - 1)
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <RemoveIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{ backgroundColor: 'white', right: 0 }}
                            element={
                                <IconButton onClick={() => {
                                    // if (fullView == true) {
                                    //     setFullView(false)
                                    //     mapElement.current.style.position = 'relative';
                                    // } else {
                                    //     setFullView(true)
                                    //     mapElement.current.style.position = 'absolute';
                                    // }
                                    dispatch(ProjectActions.SetSnackBar({
                                        open: true,
                                        message: `No action yet`,
                                        variant: 'info',
                                        duration: 6000
                                    }))
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <FullscreenIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{ backgroundColor: 'white', right: 0 }}
                            element={
                                <IconButton onClick={() => {
                                    map.getView().setZoom(13);
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <MyLocationIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{ backgroundColor: 'white', right: 0 }}
                            element={
                                <IconButton onClick={() => {

                                    if (state.projectTaskBoundries.length != 0 && map != undefined) {
                                        if (state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id)) != -1) {
                                            const index = state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id));
                                            const centroid = state.projectTaskBoundries[index].
                                                taskBoundries[state.projectTaskBoundries[index].
                                                    taskBoundries.length - 1].
                                                outline_centroid.geometry.coordinates;

                                            mainView.animate({
                                                center: centroid,
                                                duration: 2000,
                                                easing: elastic
                                            });
                                        }
                                    }

                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <GridViewIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />
                    </Stack>
                </div>
            </Stack>
        </Stack>
    )
}

export default OpenLayersMap;
