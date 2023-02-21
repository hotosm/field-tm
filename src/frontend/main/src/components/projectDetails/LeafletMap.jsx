import { Stack } from "@mui/material";
import React from "react";
import { TileLayer, Polygon, Circle, MapContainer, Marker, Popup } from 'react-leaflet';
import Map from 'map/Map';
import { useSelector } from "react-redux";
const LeafletMap = () => {

    const defaultTheme = useSelector(state => state.theme.hotTheme)
    const position = [51.505, -0.09]

    return (
        <Stack spacing={1} direction={'column'}>
            <Stack
                style={{ border: `4px solid ${defaultTheme.palette.error.main}`, }}
                justifyContent={'center'}
                height={608}
            
            >
                <Map />
            </Stack>
        </Stack>
    )
}

export default LeafletMap;