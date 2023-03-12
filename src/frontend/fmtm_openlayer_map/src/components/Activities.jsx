import { Divider, IconButton, Stack, Typography } from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import RectangleIcon from '@mui/icons-material/Rectangle';
import AccessTimeFilledIcon from '@mui/icons-material/AccessTimeFilled';
import LinkIcon from '@mui/icons-material/Link';
import IconButtonCard from "../utilities/IconButtonCard";
import { useSelector } from "react-redux";
import environment from 'fmtm/environment';
import { easeIn, easeOut } from 'ol/easing';
//Activity Model to be display in Activities panel
const Activities = ({ history, defaultTheme, mapDivPostion, map, view, state, params }) => {

    const index = state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id));

    return (
        <Stack minWidth={100} direction={'column'} spacing={1}>

            <Stack direction={'row'} spacing={2}>
                <Typography
                    variant="h2"
                >
                    {`Task #${history.taskId}`}
                </Typography>
                <RectangleIcon style={{ color: `${defaultTheme.palette.mapFeatureColors[history.status.toLowerCase()]}` }} />
            </Stack>

            <Divider color="lightgray" />

            <Stack minHeight={120} direction={'column'} spacing={2}>
                <Typography
                    variant="h2"
                    style={{ wordWrap: "break-word" }}
                >
                    {history.action_text}
                </Typography>
                <Stack direction={'row-reverse'}>
                    <IconButtonCard
                        element={
                            <IconButton onClick={async () => {
                                
                                const main = document.getElementsByClassName('mainview')[0]
                                await main.scrollTo({
                                    top: mapDivPostion
                                });

                                const centroid = state.projectTaskBoundries[index].
                                    taskBoundries.filter((task) => {
                                        return task.id == history.taskId
                                    })[0].outline_centroid.geometry.coordinates;

                                map.getView().setCenter(centroid)

                                setTimeout(() => {
                                    view.animate({ zoom: 20, easing: easeOut, duration: 2000, });
                                }, 100);


                            }}
                                color="info" aria-label="share qrcode"
                            >
                                <LinkIcon color="info" sx={{ fontSize: 30 }} />
                            </IconButton>
                        }
                    />
                </Stack>
            </Stack>

            <Divider color="lightgray" />

            <Stack direction={'row'} spacing={2}>
                <AccessTimeFilledIcon />
                <Typography
                    variant="h2"
                >
                    {history.action_date}
                </Typography>
            </Stack>

        </Stack >
    )
}
export default Activities;
