import React from "react";
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import SearchIcon from '@mui/icons-material/Search';
import { styled, alpha } from '@mui/material/styles';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import windowDimention from "../../hooks/WindowDimension";
import CustomDropdown from "../../utilities/CustomDropdown";
import { Button } from "@mui/material";
import { useSelector } from "react-redux";


//Home Filter
const HomePageFilters = () => {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    const { windowSize } = windowDimention();
    const searchableInnerStyle: any = {
        toolbar: {
            marginTop: '0.7%',
            width: 250,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        outlineBtn: {
            width: 250,
            marginTop: '0.7%',
            borderRadius: 7,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        outlineBtnXs: {
            width: '50%',
            borderRadius: 7,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        toolbarXs: {
            width: '50%',
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },

    }

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
        border: `1px solid ${theme.palette.info['main']}`,
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
            [theme.breakpoints.up('md')]: {
                width: '20ch',
            },
        },
    }));

    return (
        <Box>

            {/* Explore project typography in mobile size */}
            <Box sx={{ display: { xs: windowSize.width <= 599 ? 'flex' : 'none', md: 'none' }, justifyContent: 'center' }}>
                <Typography
                    variant="subtitle2"
                    noWrap
                    mt={'2%'}
                    ml={'3%'}
                >
                    EXPLORE PROJECTS
                </Typography>
            </Box>
            {/* <======End======> */}

            {/* full Searchables container in md,lg,xl size */}
            <Stack sx={{ display: { xs: 'none', md: 'flex', } }} direction={'row'} spacing={2} justifyContent="center">
                <Button
                    variant="outlined"
                    color="error"
                    startIcon={<AutoAwesomeIcon />}
                    style={searchableInnerStyle.outlineBtn}
                >
                    Filters
                </Button>

                <CustomDropdown
                    color={'red'}
                    appearance={'ghost'}
                    names={['Urgent Projects',
                        'Active Projects',
                        'New Projects',
                        'Old Projects',
                        'Easy Projects',
                        'Challenging Projects'
                    ]}
                    toolBarStyle={searchableInnerStyle.toolbar}
                    text={"SORT BY"}
                    size={"lg"}
                />
                <Search id="search">
                    <SearchIconWrapper>
                        <SearchIcon color="info" />
                    </SearchIconWrapper>
                    <StyledInputBase
                        placeholder="Search…"
                        inputProps={{ 'aria-label': 'search' }}
                        style={{ width: '100%' }}
                    />
                </Search>
            </Stack>
            {/* <======End======> */}

            {/* Search field in mobile size */}
            <Stack sx={{ display: { xs: 'flex', md: 'none', flexDirection: 'column', justifyContent: 'center', } }}>
                <Search id="searchXs">
                    <SearchIconWrapper>
                        <SearchIcon />
                    </SearchIconWrapper>
                    <StyledInputBase
                        placeholder="Search…"
                        inputProps={{ 'aria-label': 'search' }}
                        style={{ width: '100%' }}
                    />
                </Search>
            </Stack>
            {/* <======End======> */}

            {/* filter and sort button in mobile size */}
            <Stack spacing={1} mt={'2%'} mb={'2%'} direction={'row'} sx={{ display: { xs: 'flex', md: 'none' }, width: '100%', justifyContent: 'center' }}>
                <Button
                    variant="outlined"
                    color="error"
                    startIcon={<AutoAwesomeIcon />}
                    style={searchableInnerStyle.outlineBtnXs}
                >
                    Filters
                </Button>
                <CustomDropdown color={'red'} appearance={'ghost'} names={['Urgent Projects', 'Active Projects', 'New Projects', 'Old Projects', 'Easy Projects', 'Challenging Projects']} toolBarStyle={searchableInnerStyle.toolbarXs} text={"SORT BY"} size={"lg"} />
            </Stack>
            {/* <======End======> */}

        </Box>
    )
}

export default HomePageFilters;