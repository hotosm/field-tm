import React from "react";
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import Badge from '@mui/material/Badge';
import SearchIcon from '@mui/icons-material/Search';
import { styled, alpha } from '@mui/material/styles';
import enviroment from "../enviroment";
import DropdownUtl from "./Dropdown";
import OutlinedButton from "./OutlinedButton";
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Stack from '@mui/material/Stack';

const SearchableRow = () => {
    const searchableInnerStyle: any = {
        search: {
            backgroundColor: enviroment.sysRedColor,
            opacity: 0.8,
            marginTop: '0.7%',
            color: 'white',
            width: '15%'
        },
        searchXs: {
            backgroundColor: enviroment.sysRedColor,
            opacity: 0.8,
            marginTop: '2%',
            marginLeft: '1%',
            marginRight: '1%',
            color: 'white',
            width: '98%'
        },
        searchableBox: {
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'center'
        },
        toolbar: {
            marginTop: '0.7%',
            display: 'flex',
            justifyContent: 'center',
            width: '15%',


        },
        dropdown: {
            // backgroundColor:enviroment.sysRedColor,

            width: '100%',



        },
        outlineBtn: {
            fontSize: 14,
            padding: 8,
            width: '15%',
            marginTop: '0.7%',
            borderRadius: 7,


        },
        outlineBtnXs: {
            fontSize: 14,
            padding: 8,
            width: '49%',
            marginTop: '0.7%',
            borderRadius: 7,
            marginLeft: '1%'


        },
        toolbarXs: {
            marginTop: '0.7%',
            display: 'flex',
            justifyContent: 'center',
            width: '48%',
            marginLeft: '1%',
            marginRight: '1%'


        },
        dropdownXs: {
            // backgroundColor:enviroment.sysRedColor,
            // color:'white'
            width: '100%',


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
        color: 'inherit',
        '& .MuiInputBase-input': {
            padding: theme.spacing(1, 1, 1, 0),
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
        <Box sx={{ mb: 1 }}>
            <Stack sx={{ display: { xs: 'none', md: 'flex', } }} direction={'row'} spacing={2} justifyContent="center">
                <OutlinedButton variant={'outlined'} color={'error'} icon={<AutoAwesomeIcon />} text="Filters" style={searchableInnerStyle.outlineBtn} />
                <DropdownUtl names={['Urgent Projects', 'Active Projects', 'New Projects', 'Old Projects', 'Easy Projects', 'Challenging Projects']} toolBarStyle={searchableInnerStyle.toolbar} btnStyle={searchableInnerStyle.dropdown} text={"Sort By"} size={"lg"} />
                <Search style={searchableInnerStyle.search}>
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

            <Box sx={{ display: { xs: 'flex', md: 'none', flexDirection: 'column', justifyContent: 'center' }, width: '100%', justifyContent: 'center' }}>
                <Search style={searchableInnerStyle.searchXs}>
                    <SearchIconWrapper>
                        <SearchIcon />
                    </SearchIconWrapper>
                    <StyledInputBase
                        placeholder="Search…"
                        inputProps={{ 'aria-label': 'search' }}
                        style={{ width: '100%' }}
                    />
                </Search>
            </Box>

            <Box sx={{ display: { xs: 'flex', md: 'none' }, marginTop: '2%' }}>
                <OutlinedButton variant={'outlined'} color={'error'} icon={<AutoAwesomeIcon />} text="filters" style={searchableInnerStyle.outlineBtnXs} />
                <DropdownUtl names={['Urgent Projects', 'Active Projects', 'New Projects', 'Old Projects', 'Easy Projects', 'Challenging Projects']} toolBarStyle={searchableInnerStyle.toolbarXs} btnStyle={searchableInnerStyle.dropdownXs} text={"Sort By"} size={"lg"} />
            </Box>
        </Box>
    )
}

export default SearchableRow;