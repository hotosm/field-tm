import { Divider, Stack } from "@mui/material";
import React, { useEffect, useState } from "react";
import CustomizedText from "../../utilities/CustomizedText";
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';


const Activities = () => {



    return (
        <Stack direction={'column'} spacing={1}>
            <Stack direction={'row'} spacing={1}>
                <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} />
                <CheckBoxOutlineBlankIcon />
            </Stack>
            <Divider color="lightgray" />
            <Stack direction={'row'} spacing={2}>
                <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} />
                <CheckBoxOutlineBlankIcon />
                <CheckBoxOutlineBlankIcon />
            </Stack>
            <Divider color="lightgray" />
            <Stack direction={'row'} spacing={1}>
                <CheckBoxOutlineBlankIcon />
                <CustomizedText text={'Testing'} font={'verdana'} size={20} top={'0%'} weight={"regular"} />

            </Stack>
        </Stack>
    )
}
export default Activities;