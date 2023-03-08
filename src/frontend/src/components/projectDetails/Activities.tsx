import { Divider, Stack } from "@mui/material";
import React, { useEffect, useState } from "react";
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';

//Activity Model to be display in Activities panel
const Activities = () => {

    return (
        <Stack direction={'column'} spacing={1}>
            <Stack direction={'row'} spacing={1}>
                {/* <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} /> */}
                <CheckBoxOutlineBlankIcon />
            </Stack>
            <Divider color="lightgray" />
            <Stack direction={'row'} spacing={2}>
                {/* <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} /> */}
                <CheckBoxOutlineBlankIcon />
                <CheckBoxOutlineBlankIcon />
            </Stack>
            <Divider color="lightgray" />
            <Stack direction={'row'} spacing={1}>
                <CheckBoxOutlineBlankIcon />
                {/* <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} /> */}

            </Stack>
        </Stack>
    )
}
export default Activities;