import { Stack } from "@mui/material";
import React from "react";
import { useSelector } from "react-redux";
import MainMap from "../views/MainMap";

const OpenLayersMap = () => {
    const defaultTheme = useSelector(state => state.theme.hotTheme)
    return (
        <Stack spacing={1} direction={'column'}>
            <Stack
                style={{ border: `4px solid ${defaultTheme.palette.error.main}`, }}
                justifyContent={'center'}
                height={608}
            
            >
                <MainMap />
            </Stack>
        </Stack>
    )
}

export default OpenLayersMap;