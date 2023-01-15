import { Box, Button } from "@mui/material";
import { Stack } from "@mui/system";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import React, { useState } from "react";
import ConfirmationDialogRaw from "../../utilities/ConfirmationDialogRaw";
import CustomizedMenus from "../../utilities/CustomizedMenus";
import enviroment from "../../enviroment";



const MapDescriptionComponents = () => {
    const [open, setOpen] = useState(false)
    const [title, setTitle] = useState("")
    const onCloseDialog = () => {
        setOpen(false)
    }
    const handleClick = (event: any) => {
        setTitle(event.target.id)
        setOpen(true)
    }
    return (

        <Box sx={{ display: 'flex', flexDirection: 'row', width: '100%', mt: 2 }}>
            <Stack spacing={1} direction={'row'} justifyContent={'center'} style={{ width: '100%' }}>
                <CustomizedMenus btnName={'Description'} btnProps={{ style: { backgroundColor: 'white', color: enviroment.sysBlackColor, }, sx: { boxShadow: 2 } }} element={<div>cool</div>} />
                <CustomizedMenus btnName={'Instructions'} btnProps={{ style: { backgroundColor: 'white', color: enviroment.sysBlackColor, }, sx: { boxShadow: 2 } }} element={<div>cool</div>} />
                <CustomizedMenus btnName={'Map Legends'} btnProps={{ style: { backgroundColor: 'white', color: enviroment.sysBlackColor, }, sx: { boxShadow: 2 } }} element={<div>cool</div>} />
            </Stack>
        </Box>
    )
}

export default MapDescriptionComponents;