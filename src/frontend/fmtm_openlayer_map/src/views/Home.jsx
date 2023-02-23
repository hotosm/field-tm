import React, { useEffect } from "react";
import "../../node_modules/ol/ol.css";
import '../styles/home.css'
import { Box, Container, Divider, Stack, Typography } from '@mui/material';
import WindowDimension from "fmtm/WindowDimension";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import MapDescriptionComponents from "../components/MapDescriptionComponents";
import MapLegends from "../components/MapLegends";
import ActivitiesPanel from "../components/ActivitiesPanel";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router-dom";
import TasksComponent from "../components/TasksComponent";
import OpenLayersMap from "../components/OpenLayersMap";
import BasicTabs from "fmtm/BasicTabs";
import environment from "fmtm/environment";
import { ProjectById } from "../api/Project";
import { ProjectActions } from "../store/slices/ProjectSlice";

const Home = () => {
    const dispatch = useDispatch();
    const params = useParams();
    const defaultTheme = useSelector(state => state.theme.hotTheme)
    const state = useSelector(state => state.project.projectData)
    const encodedId = params.id

    useEffect(() => {
        if (environment.decode(encodedId) != state.id) {
            dispatch(ProjectById(`${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`))
        }else{
            console.log('i was not opened')
        }
    }, [params.id])


    const { type } = WindowDimension();

    const ProjectDetailsStyles = {
        text: {
            marginLeft: '2%'
        },
        icon: {
            marginTop: '0.5%',
            fontSize: 22
        }
    }
    const MapDetails = [
        { value: 'lock', color: 'blue', status: 'none' },
        { value: 'opened', color: 'green', status: 'lock' }
    ]

    const panelData = [
        { label: 'Activities', element: <ActivitiesPanel /> },
        { label: 'My Tasks', element: <TasksComponent type={type} /> }
    ]

    //mock data
    const descriptionData = [
        {
            value: 'Descriptions', element: <Typography align="center" >
                Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
                molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
                numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
                optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
                obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
                nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
                tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
                quia. Quo neque error repudiandae fuga? Ipsa laudantium molestias eos
                sapiente officiis modi at sunt excepturi expedita sint? Sed quibusdam
                recusandae alias error harum maxime adipisci amet laborum. Perspiciatis
                minima nesciunt dolorem! Officiis iure rerum voluptates a cumque velit
                quibusdam sed amet tempora. Sit laborum ab, eius fugit doloribus tenetur
                fugiat, temporibus enim commodi iusto libero magni deleniti quod quam
                consequuntur! Commodi minima excepturi repudiandae velit hic maxime
                doloremque. Quaerat provident commodi consectetur veniam similique ad
                earum omnis ipsum saepe, voluptas, hic voluptates pariatur est explicabo
                fugiat, dolorum eligendi quam cupiditate excepturi mollitia maiores labore
                suscipit quas? Nulla, placeat. Voluptatem quaerat non architecto ab laudantium
                modi minima sunt esse temporibus sint culpa, recusandae aliquam numquam
                totam ratione voluptas quod exercitationem fuga. Possimus quis earum veniam
                quasi aliquam eligendi, placeat qui corporis!
            </Typography>
        },
        {
            value: 'Instructions', element: <Typography align="center" >
                Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
                molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
                numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
                optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
                obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
                nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
                tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
                quia. Quo neque error repudiandae fuga? Ipsa laudantium molestias eos
                sapiente officiis modi at sunt excepturi expedita sint? Sed quibusdam
                recusandae alias error harum maxime adipisci amet laborum. Perspiciatis
                minima nesciunt dolorem! Officiis iure rerum voluptates a cumque velit
                quibusdam sed amet tempora. Sit laborum ab, eius fugit doloribus tenetur
                fugiat, temporibus enim commodi iusto libero magni deleniti quod quam
                consequuntur! Commodi minima excepturi repudiandae velit hic maxime
                doloremque. Quaerat provident commodi consectetur veniam similique ad
                earum omnis ipsum saepe, voluptas, hic voluptates pariatur est explicabo
                fugiat, dolorum eligendi quam cupiditate excepturi mollitia maiores labore
                suscipit quas? Nulla, placeat. Voluptatem quaerat non architecto ab laudantium
                modi minima sunt esse temporibus sint culpa, recusandae aliquam numquam
                totam ratione voluptas quod exercitationem fuga. Possimus quis earum veniam
                quasi aliquam eligendi, placeat qui corporis!
            </Typography>
        },
        {
            value: 'Legends',
            element:
                <MapLegends
                    direction={'column'}
                    iconProps={{}}
                    spacing={1}
                    details={MapDetails}
                    iconBtnProps={{ disabled: true }}
                    valueStatus
                />
        }
    ]

    return (
        <Stack spacing={2}>

            <Stack direction="column"
                justifyContent="center"
                alignItems={"center"}
            >
                <Stack
                    direction={'row'}
                    p={2}
                    spacing={2}
                    divider={
                        <Divider
                            sx={{ backgroundColor: defaultTheme.palette.grey['main'] }}
                            orientation="vertical"
                            flexItem
                        />}
                >
                    <Typography
                        variant="h4"
                        fontSize={defaultTheme.typography.fontSize}
                        top={'1.8%'}
                    >
                        Testing Data
                    </Typography>

                    <Typography
                        variant="h4"
                        fontSize={defaultTheme.typography.fontSize}
                        top={'1.8%'}
                    >
                        Testing Data
                    </Typography>

                </Stack>

            </Stack>

            <Stack direction={'row'} justifyContent={'center'}>
                <LocationOnIcon color='error' style={ProjectDetailsStyles.icon} />
                <Typography
                    variant="caption"
                >
                    Testing Data
                </Typography>
            </Stack>

            <Stack direction={'column'} spacing={1}>
                <MapDescriptionComponents details={descriptionData} type={type} />
                <OpenLayersMap />
            </Stack>

            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                <BasicTabs listOfData={panelData} />
            </Box>
        </Stack>
    )
}

export default Home;