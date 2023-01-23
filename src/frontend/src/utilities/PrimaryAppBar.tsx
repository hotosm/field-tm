import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import MenuIcon from '@mui/icons-material/Menu';
import Button from '@mui/material/Button';
import enviroment from '../enviroment';
import windowDimention from '../customHooks/WindowDimension';
import DrawerComponent from './CustomDrawer';
import CustomizedImage from '../utilities/CustomizedImage';
import { Link } from 'react-router-dom';



export default function PrimaryAppBar() {
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
      fontFamily: 'BarlowMedium',
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
    },
    logo: {
      width: 111,
      height: 32
    }
  }





  const { windowSize, type } = windowDimention();



  return (
    <Box sx={{ flexGrow: 1 }}>
      <DrawerComponent open={open} placement={'right'} onClose={handleOnCloseDrawer} size={type == 'xs' ? 'full' : 'xs'} />
      <AppBar position="static" style={appBarInnerStyles.appBar}>
        <Toolbar>
          <Link to={'/'}>
            <CustomizedImage status={'logo'} style={appBarInnerStyles.logo} />
          </Link>
          <Typography
            variant="h6"
            noWrap
            component="div"
            fontStyle={{ fontFamily: 'BarlowMedium' }}
            fontSize={20}
            sx={{ display: { xs: 'none', sm: 'block' } }}
            style={appBarInnerStyles.pageHeading}
          >
            EXPLORE PROJECTS
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Box sx={{ display: { md: 'flex', xs: 'none' } }}>
            <Button color="inherit" style={appBarInnerStyles.login}>Login</Button>
            <Button color="inherit" style={appBarInnerStyles.login}>Sign up</Button>
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