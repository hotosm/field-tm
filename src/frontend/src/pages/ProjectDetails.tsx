import React from "react";
import { Box, Container, Divider, Stack } from '@mui/material'
import CustomizedText from "../utilities/CustomizedText";
import enviroment from "../enviroment";

import windowDimention from "../customHooks/WindowDimension";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import LeafletMap from "../components/projectDetails/LeafletMap";
import VerticalTabs from "../components/projectDetails/BasicTabs";
import MapDescriptionComponents from "../components/projectDetails/MapDescriptionComponents";

const ProjectDetails = () => {
    const { windowSize, type } = windowDimention()
    const ProjectDetailsStyles = {
        text: {
            marginLeft: '2%'
        },
        icon: {
            marginTop: '1%',
            fontSize: 22
        }
    }

    return (
        <div>


            <Stack direction="column"
                spacing={2}
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
                <MapDescriptionComponents />
                <LeafletMap />
            </Stack>
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                <VerticalTabs />
            </Box>
        </div>
    )
}

export default ProjectDetails;