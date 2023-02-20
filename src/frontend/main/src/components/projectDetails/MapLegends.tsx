import { Box, IconButton, Typography } from "@mui/material";
import { Stack } from "@mui/system";
import React from "react";
import LockIcon from '@mui/icons-material/Lock';


const MapLegends = ({ details, direction, spacing, iconBtnProps, iconProps, valueStatus }) => {
    return (
        <Stack direction={direction} spacing={spacing}>
            {
                details.map((data, index) => {
                    return (
                        <Stack key={index} direction={'row'} spacing={1} p={1}>
                            <IconButton style={{ backgroundColor: data.color, borderRadius: 0 }} {...iconBtnProps} color="primary" aria-label="upload picture" component="label">
                                <input hidden type="button" />
                                <LockIcon style={{ color: data.status == 'lock' ? 'white' : data.status = 'disabled' ? 'lightgray' : data.color }} {...iconProps} />
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