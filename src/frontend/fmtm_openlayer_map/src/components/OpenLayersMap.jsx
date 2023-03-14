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
import FormatAlignCenterIcon from '@mui/icons-material/FormatAlignCenter';
import RemoveIcon from '@mui/icons-material/Remove';
import KeyboardDoubleArrowUpIcon from '@mui/icons-material/KeyboardDoubleArrowUp';
import KeyboardDoubleArrowDownIcon from '@mui/icons-material/KeyboardDoubleArrowDown';
import '../styles/home.scss'
import { ProjectActions } from "../store/slices/ProjectSlice";
import { HomeActions } from 'fmtm/HomeSlice';



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
        environment,
        mapDivPostion,
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
                        title={`Task #${taskId}`}
                        onClose={() => {
                            dispatch(HomeActions.SetDialogStatus(false))
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
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
                            element={
                                <IconButton onClick={() => {
                                    const main = document.getElementsByClassName('mainview')[0]
                                    main.scrollTo({
                                        top: mapDivPostion
                                    });
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <KeyboardDoubleArrowUpIcon color="error" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
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
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
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
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
                            element={
                                <IconButton onClick={() => {
                                    // if (fullView == true) {
                                    //     setFullView(false)
                                    //     mapElement.current.style.position = 'relative';
                                    // } else {
                                    //     setFullView(true)
                                    //     mapElement.current.style.position = 'absolute';
                                    // }
                                    dispatch(HomeActions.SetSnackBar({
                                        open: true,
                                        message: `No action yet`,
                                        variant: 'warning',
                                        duration: 3000
                                    }))
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <FullscreenIcon color="info" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
                            element={
                                <IconButton onClick={() => {
                                    map.getView().setZoom(15);
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <MyLocationIcon color="warning" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
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

                                    map.getTargetElement().classList.remove('spinner');

                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <GridViewIcon color="success" sx={{ fontSize: 30 }} />
                                </IconButton>
                            }
                        />

                        <IconButtonCard
                            style={{
                                backgroundColor:
                                    defaultTheme.palette.primary['primary_rgb'],
                                right: 0
                            }}
                            radius={0}
                            element={
                                <IconButton onClick={() => {
                                    const main = document.getElementsByClassName('mainview')[0]
                                    const index = state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id));
                                    let taskHistories = [];
                                    state.projectTaskBoundries[index].taskBoundries.forEach((task) => {
                                        taskHistories = taskHistories.concat(task.task_history.map(history => {
                                            return { ...history, taskId: task.id, status: task.task_status_str }
                                        }))
                                    })

                                    if (taskHistories.length > 1) {
                                        main.scrollTo(0, document.getElementsByClassName('mainview')[0].scrollHeight / 6);
                                    } else {
                                        main.scrollTo(0, document.getElementsByClassName('mainview')[0].scrollHeight);
                                    }

                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <KeyboardDoubleArrowDownIcon color="error" sx={{ fontSize: 30 }} />
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
