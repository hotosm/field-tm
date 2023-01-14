import { Box, Button, Stack } from "@mui/material";
import { style } from "@mui/system";
import React from "react";
import { TileLayer, Polygon, Circle, MapContainer, Marker, Popup } from 'react-leaflet';
import enviroment from "../../enviroment";
import ColorTabs from "./BasicTabs";
import CustomDropdown from "../../utilities/CustomDropdown";
import CustomizedText from "../../utilities/CustomizedText";
import SelectTextField from "../../utilities/ConfirmationDialogRaw";
import ConfirmationDialogRaw from "../../utilities/ConfirmationDialogRaw";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';

const LeafletMap = () => {
    const MapStyles = {
        toolbar: {
            marginTop: '0.7%',
            display: 'flex',
            justifyContent: 'center',
            width: '15%',
            fontFamily: 'BarlowMedium',

        },
        dropdown: {
            fontFamily: 'BarlowMedium',
            width: '100%',
            color: 'black'
        },
    }
    const position: any = [51.505, -0.09]

    return (
        <Stack spacing={1} direction={'column'}>

            {/* <CustomizedText text={"Choose the task from the map"} size={16} font={enviroment.mediumText} weight={'bold'} top={'0%'} /> */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', border: '4px solid red', height: 500 }}>
                <MapContainer style={{ opacity: 0.9 }} attributionControl={false} center={position} zoom={13} scrollWheelZoom={false} >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={position}>
                        <Popup>
                            A pretty CSS3 popup. <br /> Easily customizable.
                        </Popup>
                    </Marker>
                </MapContainer>
            </div>
        </Stack>
    )
}

export default LeafletMap;