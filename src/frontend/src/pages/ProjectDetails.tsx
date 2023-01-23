import React from "react";
import { Box, Container, Divider, Stack, Typography } from '@mui/material'
import CustomizedText from "../utilities/CustomizedText";
import enviroment from "../enviroment";

import windowDimention from "../customHooks/WindowDimension";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import LeafletMap from "../components/projectDetails/LeafletMap";

import MapDescriptionComponents from "../components/projectDetails/MapDescriptionComponents";
import BasicTabs from "../components/projectDetails/BasicTabs";
import MapLegends from "../components/projectDetails/MapLegends";

const ProjectDetails = () => {
    const { type } = windowDimention()
    const ProjectDetailsStyles = {
        text: {
            marginLeft: '2%'
        },
        icon: {
            marginTop: '1%',
            fontSize: 22
        }
    }
    const MapDetails: any = [{ value: 'lock', color: 'blue', status: 'none' }, { value: 'opened', color: 'green', status: 'lock' }]
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
        <div>
            <Stack direction="column"
                spacing={0}
                justifyContent="center"
                alignItems={"center"}
            >
                <Stack direction={'row'} p={2} spacing={2} divider={<Divider sx={{ backgroundColor: enviroment.sysBlackColor }} orientation="vertical" flexItem />}>
                    <CustomizedText font={enviroment.regularText} top={'1.8%'} size={16} text={'Testing Data'} weight={'regular'} />
                    <CustomizedText font={enviroment.regularText} top={'1.8%'} size={16} text={'Testing Data'} weight={'regular'} />
                </Stack>
                <CustomizedText font={enviroment.headerText} top={'0%'} size={20} text={'OpenStreetMap Bangladesh-Earthquake'} weight={'regular'} />
            </Stack>

            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }} mb={'1%'}>
                <LocationOnIcon color='error' style={ProjectDetailsStyles.icon} />
                <CustomizedText font={enviroment.mediumText} top={'1%'} size={16} text={'Testing Data'} weight={'regular'} />
            </Box>
            <Stack direction={'column'} spacing={1}>
                <MapDescriptionComponents details={descriptionData} type={type} />
                <LeafletMap />
            </Stack>
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                <BasicTabs />
            </Box>
        </div>
    )
}

export default ProjectDetails;