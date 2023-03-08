import { Box, Typography } from "@mui/material";
import { Stack } from "@mui/system";
import React from "react";
import { useSelector } from "react-redux";
import CustomizedMenus from "fmtm/CustomizedMenus";
import MapLegends from "./MapLegends";


const MapDescriptionComponents = ({ type, state, defaultTheme }) => {

    const descriptionData = [
        {
            value: 'Descriptions', element: <Typography align="center" >
                {state.projectInfo.description}
            </Typography>
        },
        {
            value: 'Instructions', element: <Typography align="center" >
                {state.projectInfo.location_str}
            </Typography>
        },
        {
            value: 'Legends',
            element:
                <MapLegends
                    direction={'column'}
                    defaultTheme={defaultTheme}
                    spacing={1}
                    iconBtnProps={{ disabled: true }}
                    valueStatus
                />
        }
    ]
    return (

        <Box sx={{ display: 'flex', flexDirection: 'row', width: '100%', mt: 1 }}>
            <Stack
                width={'100%'}
                p={1}
                spacing={type == 's' ? 1 : type == 'xs' ? 1 : 3}
                direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'}
                justifyContent={'center'}
            >
                {
                    descriptionData.map((data, index) => {
                        return (
                            <CustomizedMenus
                                key={index}
                                btnName={data.value}
                                btnProps={{
                                    style: {
                                        //overidding style
                                        backgroundColor: 'white',
                                        fontFamily: defaultTheme.typography.h1.fontFamily,
                                        fontSize: 16

                                    },
                                    color: 'primary',
                                    sx: { boxShadow: 2 }
                                }}
                                element={data.element}
                            />
                        )
                    })
                }
            </Stack>
        </Box>
    )
}

export default MapDescriptionComponents;