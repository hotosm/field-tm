import { Box, Grid, Pagination, Paper, Stack, Typography } from "@mui/material";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { experimentalStyled as styled } from '@mui/material/styles';
import BasicCard from "fmtm/BasicCard";
import Activities from "./Activities";
import environment from "fmtm/environment";
import InputBase from '@mui/material/InputBase';
import SearchIcon from '@mui/icons-material/Search';
import { alpha } from '@mui/material/styles';

// const Item = styled(Paper)(({ theme }) => ({
//     backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
//     ...theme.typography.body2,
//     padding: theme.spacing(2),
//     textAlign: 'center',
//     color: theme.palette.text.secondary,
// }));

const Search = styled('div')(({ theme }) => ({
    position: 'relative',
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.common.white, 0.15),
    '&:hover': {
        backgroundColor: alpha(theme.palette.common.white, 0.25),
    },
    marginRight: theme.spacing(2),
    marginLeft: 0,
    opacity: 0.8,
    border: `1px solid ${theme.palette.warning['main']}`,
    width: '100%',
    [theme.breakpoints.up('sm')]: {
        marginLeft: theme.spacing(3),
        width: 'auto',
    },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
    padding: theme.spacing(0, 2),
    height: '100%',
    position: 'absolute',
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
    color: 'primary',
    '& .MuiInputBase-input': {
        padding: theme.spacing(1, 1, 1, 0),
        fontFamily: theme.typography.h3.fontFamily,
        // vertical padding + font size from searchIcon
        paddingLeft: `calc(1em + ${theme.spacing(4)})`,
        transition: theme.transitions.create('width'),
        width: '100%',
        // [theme.breakpoints.up('md')]: {
        //     width: '20ch',
        // },
    },
}));




const ActivitiesPanel = ({ defaultTheme, state, params, map, view, mapDivPostion, states }) => {

    const displayLimit = 10;
    const [searchText, setSearchText] = useState('')
    const [taskHistories, setTaskHistories] = useState([])
    const [paginationSize, setPaginationSize] = useState(0)
    const [taskDisplay, setTaskDisplay] = React.useState(displayLimit)
    const [allActivities, setAllActivities] = useState(0)
    const [prev, setPrv] = React.useState(0)


    const handleChange = (event, value) => {
        setPrv(((value * displayLimit) - displayLimit))
        setTaskDisplay(value * displayLimit)
    };

    const handleOnchange = (event) => {
        setSearchText(event.target.value)
    }

    useEffect(() => {

        const index = state.findIndex(project => project.id == environment.decode(params.id));
        let taskHistories = [];


        if (index != -1) {
            state[index].taskBoundries.forEach((task) => {
                taskHistories = taskHistories.concat(task.task_history.map(history => {
                    return { ...history, taskId: task.id, status: task.task_status_str }
                }))
            })
        }

        let finalTaskHistory = taskHistories.filter((task) => {
            return task.taskId.toString().includes(searchText) || task.action_text.split(':')[1].replace(/\s+/g, '').toString().includes(searchText.toString())
        })

        if (searchText != '') {

            setAllActivities(finalTaskHistory.length)
            const tasksToDisplay = finalTaskHistory.filter((task, index) => {
                return index <= taskDisplay - 1 && index >= prev
            })
            setTaskHistories(tasksToDisplay)
            const paginationSize =
                finalTaskHistory.length % displayLimit == 0 ? Math.floor(finalTaskHistory.length / displayLimit)
                    : (Math.floor(finalTaskHistory.length / displayLimit) + 1)
            setPaginationSize(paginationSize)

        } else {

            setAllActivities(taskHistories.length)
            const tasksToDisplay = taskHistories.filter((task, index) => {
                return index <= taskDisplay - 1 && index >= prev
            })

            setTaskHistories(tasksToDisplay)
            const paginationSize =
                taskHistories.length % displayLimit == 0 ? Math.floor(taskHistories.length / displayLimit)
                    : (Math.floor(taskHistories.length / displayLimit) + 1)
            setPaginationSize(paginationSize)
        }


    }, [taskDisplay, searchText])

    return (
        <Stack spacing={2}>
            <Typography
                variant="h1"
                fontSize={defaultTheme.typography.htmlFontSize}
                color={defaultTheme.palette.info['main']}
            >
                {`Total Activities ${allActivities}`}
            </Typography>

            <Search id="searchActivities">
                <SearchIconWrapper>
                    <SearchIcon color="info" />
                </SearchIconWrapper>
                <StyledInputBase
                    placeholder="Search by Task Id and username…"
                    inputProps={{ 'aria-label': 'search' }}
                    style={{ width: '100%' }}
                    onChange={handleOnchange}
                />
            </Search>

            <Grid container item columns={{ xs: 2, sm: 3, md: 7 }}>
                <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 1, sm: 3, md: 4, lg: 6, xl: 7 }}>
                    {taskHistories.map((history, index) => (
                        <Grid item xs={1} sm={1} md={1} lg={1} xl={1} key={index}>
                            <BasicCard
                                key={index}
                                title={{}}
                                subtitle={{}}
                                contentProps={{}}
                                variant={'elevation'}
                                headerStatus={false}
                                content={
                                    <Activities
                                        defaultTheme={defaultTheme}
                                        history={history}
                                        map={map}
                                        view={view}
                                        mapDivPostion={mapDivPostion}
                                        state={states}
                                        params={params}
                                    />}
                            />
                        </Grid>
                    ))}
                </Grid>
            </Grid>

            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1%' }}>
                <Pagination onChange={handleChange} color="standard" count={paginationSize} variant="outlined" />
            </Box>
        </Stack>
    )
}

export default ActivitiesPanel;
