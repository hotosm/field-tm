import { Box, Button } from "@mui/material";
import { Stack } from "@mui/system";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import React, { useState } from "react";
import ConfirmationDialogRaw from "../../utilities/ConfirmationDialogRaw";



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

        <Box sx={{ display: 'flex', flexDirection: 'row', width: '100%' }}>
            <Stack spacing={2} direction={'row'} justifyContent={'center'} style={{ width: '100%' }}>
                <Button id="0" onClick={handleClick} endIcon={<KeyboardArrowDownIcon />} style={{ borderRadius: 0, color: 'black' }}>Description</Button>
                <Button id="1" onClick={handleClick} endIcon={<KeyboardArrowDownIcon />} style={{ borderRadius: 0, color: 'black' }}>Instructions</Button>
                <Button id="2" onClick={handleClick} endIcon={<KeyboardArrowDownIcon />} style={{ borderRadius: 0, color: 'black' }}>Map Legends</Button>
                <ConfirmationDialogRaw open={open} value={title} keepMounted={false} id={"1"} onClose={onCloseDialog} />
            </Stack>
        </Box>
    )
}

export default MapDescriptionComponents;