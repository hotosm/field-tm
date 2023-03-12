
import React, { useState } from "react";
import IconButtonCard from "../utilities/IconButtonCard";
import BasicDialog from "../utilities/BasicDialog";
import DialogActions from "../components/DialogActions";
import '../styles/home.scss'
import { HomeActions } from 'fmtm/HomeSlice';
import CoreModules from 'fmtm/CoreModules';
import AssetModules from 'fmtm/AssetModules';


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
    const dispatch = CoreModules.useDispatch();
    const [fullView, setFullView] = useState(false)
    return (
        <CoreModules.Stack spacing={1} direction={'column'}>
            <CoreModules.Stack
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

                    <CoreModules.Stack
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
                                <CoreModules.IconButton onClick={() => {
                                    const main = document.getElementsByClassName('mainview')[0]
                                    main.scrollTo({
                                        top: mapDivPostion
                                    });
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <AssetModules.KeyboardDoubleArrowUpIcon color="error" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {
                                    let actualZoom = map.getView().getZoom();
                                    map.getView().setZoom(actualZoom + 1)
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <AssetModules.AddIcon color="info" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {
                                    let actualZoom = map.getView().getZoom();
                                    map.getView().setZoom(actualZoom - 1)
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <AssetModules.RemoveIcon color="info" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {
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
                                    <AssetModules.FullscreenIcon color="info" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {
                                    map.getView().setZoom(15);
                                }}
                                    color="info" aria-label="share qrcode"
                                >
                                    <AssetModules.MyLocationIcon color="warning" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {

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
                                    <AssetModules.GridViewIcon color="success" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
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
                                <CoreModules.IconButton onClick={() => {
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
                                    <AssetModules.KeyboardDoubleArrowDownIcon color="error" sx={{ fontSize: 30 }} />
                                </CoreModules.IconButton>
                            }
                        />
                    </CoreModules.Stack>
                </div>
            </CoreModules.Stack>
        </CoreModules.Stack>
    )
}

export default OpenLayersMap;
