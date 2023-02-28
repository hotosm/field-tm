import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import MenuIcon from '@mui/icons-material/Menu';
import Button from '@mui/material/Button';
import windowDimention from '../hooks/WindowDimension';
import DrawerComponent from './CustomDrawer';
import CustomizedImage from '../utilities/CustomizedImage';
import { Link, RouterProvider } from 'react-router-dom';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import { useDispatch, useSelector } from 'react-redux';
import { ThemeActions } from '../store/slices/ThemeSlice';


export default function PrimaryAppBar() {

  const [open, setOpen] = React.useState<boolean>(false);
  const [brightness, setBrightness] = React.useState<boolean>(true)
  const dispatch = useDispatch();
  const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme);

  const handleOpenDrawer = () => {
    setOpen(true)
  }




  const handleOnCloseDrawer = () => {
    setOpen(false)
  }

  const handleLightToggle = () => {
    setBrightness(!brightness)

    const newTheme = {
      ...defaultTheme,
      palette: {
        ...defaultTheme.palette,
        mode: !brightness == true ? 'light' : 'dark'
      }
    }
    console.log({ ...defaultTheme, mode: 'dark' })
    dispatch(ThemeActions.UpdateBrightness(newTheme))
  }

  const appBarInnerStyles = {
    logo: {
      width: 111,
      height: 32
    },
    btnLogin: {
      fontSize: defaultTheme.typography.h3.fontSize,
    }
  }
  const { type } = windowDimention();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <DrawerComponent
        open={open}
        placement={'right'}
        onClose={handleOnCloseDrawer}
        size={type == 'xs' ? 'full' : 'xs'}
      />
      <AppBar position="static">
        <Toolbar>

          <Link to={'/'}>
            <CustomizedImage status={'logo'} style={appBarInnerStyles.logo} />
          </Link>
          <Typography
            variant="subtitle2"
            color={'info'}
            noWrap
            sx={{ display: { xs: 'none', sm: 'block', } }}
            ml={'3%'}
          >
            EXPLORE PROJECTS
          </Typography>


          <Box sx={{ flexGrow: 1 }} />
          <Box >
            <IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleLightToggle}
              color="inherit"
            >
              {brightness != true ? <LightModeIcon /> :
                <DarkModeIcon />
              }
            </IconButton>
          </Box>

          <Box sx={{ display: { md: 'flex', xs: 'none' } }}>
            <Button
              className='btnLogin'
              style={appBarInnerStyles.btnLogin}
              color="info"
              href="/login" >
              Login
            </Button>

            <Button
              className='btnSignUp'
              style={appBarInnerStyles.btnLogin}
              color="info" 
              href="/signup">
              Sign up
            </Button>
          </Box>
          <Box >
            <IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleOpenDrawer}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

    </Box>
  );
}
