import { Box } from "@mui/material";
import { Stack } from "@mui/system";
import React from "react";
import { useSelector } from "react-redux";
import CustomizedMenus from "../../utilities/CustomizedMenus";


const MapDescriptionComponents = ({ details, type }) => {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    return (

        <Box sx={{ display: 'flex', flexDirection: 'row', width: '100%', mt: 2 }}>
            <Stack
                width={'100%'}
                p={2}
                spacing={type == 's' ? 1 : type == 'xs' ? 1 : 3}
                direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'}
                justifyContent={'center'}
            >
                {
                    details.map((data, index) => {
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