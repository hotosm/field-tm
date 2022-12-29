import * as React from 'react';

import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';

import MenuItem from '@mui/material/MenuItem';
import Menu from '@mui/material/Menu';
import MenuIcon from '@mui/icons-material/Menu';

import AccountCircle from '@mui/icons-material/AccountCircle';
import MailIcon from '@mui/icons-material/Mail';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MoreIcon from '@mui/icons-material/MoreVert';
import Button from '@mui/material/Button';
import enviroment from '../enviroment';
import windowDimention from '../customHooks/WindowDimension';
import DrawerComponent from './Drawer';



export default function PrimarySearchAppBar() {
  const [c, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [open, setOpen] = React.useState<boolean>(false);


  const handleOpenDrawer = () => {
    setOpen(true)
  }

  const handleOnCloseDrawer = () => {
    setOpen(false)
  }


  const appBarInnerStyles = {

    appBar: {
      backgroundColor: 'white'
    },

    menu: {
      backgroundColor: 'black'
    },

    login: {
      backgroundColor: 'white', marginRight: '10%',
      color: enviroment.sysBlackColor,
      width: 100
    },

    logoText: {
      color: enviroment.sysRedColor
    },



    iconButton: {
      backgroundColor: 'white',
      color: enviroment.sysBlackColor
    },
    pageHeading: {
      color: enviroment.sysBlackColor,
      marginLeft: '3%'
    }
  }





  const { windowSize, type } = windowDimention();



  return (
    <Box sx={{ flexGrow: 1 }}>
      <DrawerComponent open={open} placement={'right'} onClose={handleOnCloseDrawer} size={type == 'xs' ? 'full' : 'xs'} />
      <AppBar position="static" style={appBarInnerStyles.appBar}>
        <Toolbar>
          <Typography
            variant="h4"
            noWrap
            component="div"
            fontStyle={{ fontFamily: 'RoughpenBold', }}
            sx={{
              display: { xs: 'none', sm: 'block' }
            }}
            style={appBarInnerStyles.logoText}
          >
            FMTM
          </Typography>

          <Typography
            variant="h6"
            noWrap
            component="div"
            fontStyle={{ fontFamily: 'RoyalLodge' }}
            sx={{ display: { xs: 'none', sm: 'block' } }}
            style={appBarInnerStyles.pageHeading}
          >
            EXPLORE PROJECTS
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Box sx={{ display: { md: 'flex', xs: 'none' } }}>
            <Button color="inherit" style={appBarInnerStyles.login}>Login</Button>
            <Button color="inherit" style={appBarInnerStyles.login}>Sign up</Button>
            {/* <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls={menuId}
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
              style={appBarInnerStyles.iconButton}
            >
              <AccountCircle />
            </IconButton> */}
          </Box>
          <Box >


            <IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleOpenDrawer}
              color="inherit"
              style={appBarInnerStyles.iconButton}
            >
              <MenuIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

    </Box>
  );
}