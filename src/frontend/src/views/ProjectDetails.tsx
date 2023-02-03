import React from "react";
import { Box, Container, Divider, Stack, Typography } from '@mui/material'
import windowDimention from "../hooks/WindowDimension";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import LeafletMap from "../components/projectDetails/LeafletMap";
import MapDescriptionComponents from "../components/projectDetails/MapDescriptionComponents";
import BasicTabs from "../utilities/BasicTabs";
import MapLegends from "../components/projectDetails/MapLegends";
import ActivitiesPanel from "../components/projectDetails/ActivitiesPanel";
import TasksComponent from "../components/projectDetails/TasksPanel";
import defaultTheme from "../themes/defaultTheme";

const ProjectDetails = () => {

    const { type } = windowDimention();
    const viewMode = type == 'xl' ? 6 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1
    const ProjectDetailsStyles = {
        text: {
            marginLeft: '2%'
        },
        icon: {
            marginTop: '0.5%',
            fontSize: 22
        }
    }
    const MapDetails: any = [
        { value: 'lock', color: 'blue', status: 'none' },
        { value: 'opened', color: 'green', status: 'lock' }
    ]

    const panelData: any = [
        { label: 'Activities', element: <ActivitiesPanel viewMode={viewMode} /> },
        { label: 'My Tasks', element: <TasksComponent type={type} /> }
    ]

    //mock data
    const descriptionData: any = [
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
                <LeafletMap />
            </Stack>

            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                <BasicTabs listOfData={panelData} />
            </Box>
        </Stack>
    )
}

export default ProjectDetails;