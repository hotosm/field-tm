import { Box, IconButton, Typography } from "@mui/material";
import { Stack } from "@mui/system";
import React from "react";
import LockIcon from '@mui/icons-material/Lock';


const MapLegends = ({ direction, spacing, iconBtnProps, defaultTheme, valueStatus }) => {

    const MapDetails = [
        {
            value: 'Ready',
            color: defaultTheme.palette.mapFeatureColors.ready,
            status: 'none'
        },
        {
            value: 'Locked For Mapping',
            color: defaultTheme.palette.mapFeatureColors.locked_for_mapping,
            status: 'lock'
        },
        {
            value: 'Locked For Validation',
            color: defaultTheme.palette.mapFeatureColors.locked_for_validation,
            status: 'lock'
        },
        {
            value: 'Ready For Validation',
            color: defaultTheme.palette.mapFeatureColors.mapped,
            status: 'none'
        },
        {
            value: 'Validated',
            color: defaultTheme.palette.mapFeatureColors.validated,
            status: 'none'
        },
        {
            value: 'Bad',
            color: defaultTheme.palette.mapFeatureColors.bad,
            status: 'none'
        },
        {
            value: 'More mapping needed',
            color: defaultTheme.palette.mapFeatureColors.invalidated,
            status: 'none'
        }
    ]
    return (
        <Stack direction={direction} spacing={spacing}>
            {
                MapDetails.map((data, index) => {
                    return (
                        <Stack key={index} direction={'row'} spacing={1} p={1}>
                            <IconButton style={{ backgroundColor: data.color, borderRadius: 0 }} {...iconBtnProps} color="primary" component="label">
                                <LockIcon style={{ color: data.status == 'none' ? data.color : 'white' }} />
                            </IconButton>
                            {
                                valueStatus && <Box style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                                    <Typography>
                                        {data.value}
                                    </Typography>
                                </Box>
                            }
                        </Stack>
                    )
                })
            }
        </Stack>
    )
}

export default MapLegends;
