import React, { useEffect, useRef, useState } from "react";
import "../../node_modules/ol/ol.css";
import '../styles/home.scss'
import { Box, Divider, Stack, Typography } from '@mui/material';
import WindowDimension from "fmtm/WindowDimension";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import MapDescriptionComponents from "../components/MapDescriptionComponents";
import ActivitiesPanel from "../components/ActivitiesPanel";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router-dom";
import TasksComponent from "../components/TasksComponent";
import OpenLayersMap from "../components/OpenLayersMap";
import BasicTabs from "fmtm/BasicTabs";
import environment from "fmtm/environment";
import { ProjectById } from "../api/Project";
import { ProjectActions } from "../store/slices/ProjectSlice";
import CustomizedSnackbar from 'fmtm/CustomizedSnackbar'
import { defaults } from "ol/control/defaults";
import OnScroll from 'fmtm/OnScroll';
import { Tile as TileLayer } from 'ol/layer.js';
import { OSM } from 'ol/source.js';
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import TasksLayer from "../layers/TasksLayer";
import { easeIn, easeOut } from 'ol/easing';
import Map from 'ol/Map'
import View from 'ol/View'
import { HomeActions } from 'fmtm/HomeSlice';
const Home = () => {

    const dispatch = useDispatch();
    const params = useParams();
    const defaultTheme = useSelector(state => state.theme.hotTheme)
    const state = useSelector(state => state.project)
    const projectInfo = useSelector(state => state.home.selectedProject)
    const stateDialog = useSelector(state => state.home.dialogStatus)
    const stateSnackBar = useSelector(state => state.home.snackbar)
    const [taskId, setTaskId] = useState()
    const mapElement = useRef();
    const [map, setMap] = useState()
    const [mainView, setView] = useState()
    const [featuresLayer, setFeaturesLayer] = useState()
    const [top, setTop] = useState(0)
    const encodedId = params.id
    const { windowSize, type } = WindowDimension();
    const { y } = OnScroll(map, windowSize.width);
    const panelData = [
        {
            label: 'Activities', element:
                <ActivitiesPanel
                    params={params}
                    state={state.projectTaskBoundries}
                    defaultTheme={defaultTheme}
                    map={map}
                    view={mainView}
                    mapDivPostion={y}
                    states={state}
                />
        },
        {
            label: 'My Tasks',
            element:
                <TasksComponent
                    defaultTheme={defaultTheme}
                    state={state.projectTaskBoundries}
                    type={type}
                />
        }
    ]

    //snackbar handle close funtion
    const handleClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        dispatch(HomeActions.SetSnackBar({
            open: false,
            message: stateSnackBar.message,
            variant: stateSnackBar.variant,
            duration: 0
        }))
    };

    //Fetch project for the first time
    useEffect(() => {
        if (state.projectTaskBoundries.findIndex(project => project.id == environment.decode(encodedId)) == -1) {
            dispatch(
                ProjectById(`${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`, state.projectTaskBoundries),
                state.projectTaskBoundries
            )
        }
        if (Object.keys(state.projectInfo).length == 0) {
            dispatch(ProjectActions.SetProjectInfo(projectInfo))
        } else {
            if (state.projectInfo.id != environment.decode(encodedId)) {
                dispatch(ProjectActions.SetProjectInfo(projectInfo))
            }
        }
    }, [params.id])


    useEffect(() => {

        const initalFeaturesLayer = new VectorLayer({
            source: new VectorSource()
        })

        const view = new View({
            projection: 'EPSG:4326',
            center: [0, 0],
            zoom: 4,
        });

        const initialMap = new Map({
            target: mapElement.current,
            controls: new defaults({
                attribution: false,
                zoom: false,
            }),
            layers: [
                new TileLayer({
                    source: new OSM(),
                    visible: true
                }),
                initalFeaturesLayer
            ],
            view: view
        })

        initialMap.on('click', function (event) {
            initialMap.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
                const status = feature.getId().replace("_", ",").split(',')[1]
                if (environment.tasksStatus.findIndex(data => data.key == status) != -1) {
                    setFeaturesLayer(feature)
                    setTaskId(feature.getId().split('_')[0])
                    dispatch(HomeActions.SetDialogStatus(true))
                }
            });
        });

        initialMap.on('loadstart', function () {
            initialMap.getTargetElement().classList.add('spinner');
        });

        setMap(initialMap)
        setView(view)
        setFeaturesLayer(initalFeaturesLayer)

    }, [])


    useEffect(() => {
        if (map != undefined) {
            const topX = map.getTargetElement().getBoundingClientRect().y;
            setTop(topX)
        }
    }, [map, y])

    TasksLayer(map, mainView, featuresLayer)



    return (
        <Stack spacing={2}>

            {/* Home snackbar */}
            <CustomizedSnackbar
                duration={stateSnackBar.duration}
                open={stateSnackBar.open}
                variant={stateSnackBar.variant}
                message={stateSnackBar.message}
                handleClose={handleClose}
            />

            {/* Top project details heading medium dimension*/}
            <Stack
                sx={{ display: { md: 'flex', xs: 'none' } }}
                direction="column"
                justifyContent="center"
                spacing={5}
                alignItems={"center"}
            >

                <Stack direction={'row'} p={2} spacing={2}
                    divider={
                        <Divider
                            sx={{ backgroundColor: defaultTheme.palette.grey['main'] }}
                            orientation="vertical"
                            flexItem
                        />
                    }
                >
                    <Stack direction={'row'} justifyContent={'center'}>
                        <LocationOnIcon color='error' style={{ fontSize: 22 }} />
                        <Typography variant="h1" >
                            {state.projectInfo.title}
                        </Typography>
                    </Stack>

                    <Stack>
                        <Typography
                            variant="h4"
                            fontSize={defaultTheme.typography.fontSize}
                        >
                            {`#${state.projectInfo.id}`}
                        </Typography>
                    </Stack>

                    <Stack mt={'5%'} >
                        <Typography
                            variant="h4"
                            fontSize={defaultTheme.typography.fontSize}
                            color={defaultTheme.palette.warning['main']}
                        >
                            {state.projectInfo.priority_str}
                        </Typography>
                    </Stack>

                </Stack>
            </Stack>


            {/* project Details Title */}
            <Stack sx={{ display: { xs: 'flex', md: 'none' } }} spacing={2}>

                <Stack direction={'row'} justifyContent={'center'}>
                    <LocationOnIcon color='error' style={{ marginTop: '1.5%', fontSize: 22 }} />
                    <Typography variant="caption" >
                        {state.projectInfo.title}
                    </Typography>
                </Stack>

                <Stack direction={'row'} justifyContent={'center'}>
                    <Typography
                        variant="h1"
                        fontSize={defaultTheme.typography.fontSize}
                    >
                        {`#${state.projectInfo.id}`}
                    </Typography>
                </Stack>

                <Stack direction={'row'} justifyContent={'center'}>
                    <Typography
                        variant="h1"
                        fontSize={defaultTheme.typography.fontSize}
                        color={defaultTheme.palette.warning['main']}
                    >
                        {state.projectInfo.priority_str}
                    </Typography>
                </Stack>

            </Stack>

            {/* Center descriptin and map */}
            <Stack direction={'column'} spacing={1}>
                <MapDescriptionComponents defaultTheme={defaultTheme} state={state} type={type} />
                <OpenLayersMap
                    defaultTheme={defaultTheme}
                    stateDialog={stateDialog}
                    params={params}
                    state={state}
                    taskId={taskId}
                    top={top}
                    featuresLayer={featuresLayer}
                    map={map}
                    mainView={mainView}
                    mapElement={mapElement}
                    environment={environment}
                    mapDivPostion={y}
                />
            </Stack>


            {/* project Details Tabs */}
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                <BasicTabs listOfData={panelData} />
            </Box>

        </Stack>
    )
}

export default Home;
