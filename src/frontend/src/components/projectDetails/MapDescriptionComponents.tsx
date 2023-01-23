import { Box, Button } from "@mui/material";
import { Stack } from "@mui/system";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import React, { useState } from "react";
import ConfirmationDialogRaw from "../../utilities/ConfirmationDialogRaw";
import CustomizedMenus from "../../utilities/CustomizedMenus";
import enviroment from "../../enviroment";



const MapDescriptionComponents = ({ details, type }) => {
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
            <Stack spacing={type == 's' ? 1 : type == 'xs' ? 1 : 3} direction={'row'} justifyContent={'center'} style={{ width: '100%' }}>
                {
                    details.map((data, index) => {
                        return (
                            <CustomizedMenus
                                key={index}
                                btnName={data.value}
                                btnProps={{
                                    style: {
                                        backgroundColor: 'white',
                                        color: enviroment.sysBlackColor,
                                        fontFamily: enviroment.mediumText,
                                        fontSize: type == 's' ? 14 : type == 'xs' ? 14 : 16
                                    },
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