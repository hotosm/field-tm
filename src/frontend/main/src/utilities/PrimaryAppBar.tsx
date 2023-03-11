import * as React from 'react';
import windowDimention from '../hooks/WindowDimension';
import DrawerComponent from './CustomDrawer';
import CustomizedImage from '../utilities/CustomizedImage';
import { ThemeActions } from '../store/slices/ThemeSlice';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';

export default function PrimaryAppBar() {
  const [open, setOpen] = React.useState<boolean>(false);
  const [brightness, setBrightness] = React.useState<boolean>(true)
  const dispatch = CoreModules.useDispatch();
  const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme);

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
    <CoreModules.Box sx={{ flexGrow: 1 }}>
      <DrawerComponent
        open={open}
        placement={'right'}
        onClose={handleOnCloseDrawer}
        size={type == 'xs' ? 'full' : 'xs'}
      />
      <CoreModules.AppBar position="static">
        <CoreModules.Toolbar>

          <CoreModules.Link to={'/'}>
            <CustomizedImage status={'logo'} style={appBarInnerStyles.logo} />
          </CoreModules.Link>

          <CoreModules.Link style={
            {
              marginLeft: '3%',
              textDecoration: 'none',
              color: defaultTheme.palette.info.main
            }
          } to={'/'}>
            <CoreModules.Typography
              variant="subtitle2"
              color={'info'}
              noWrap
              sx={{ display: { xs: 'none', sm: 'block', } }}
              ml={'3%'}
            >
              EXPLORE PROJECTS
            </CoreModules.Typography>

          </CoreModules.Link>

          <CoreModules.Box sx={{ flexGrow: 1 }} />
          <CoreModules.Box >
            <CoreModules.IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleLightToggle}
              color="inherit"
            >
              {brightness != true ? <AssetModules.LightModeIcon /> :
                <AssetModules.DarkModeIcon />
              }
            </CoreModules.IconButton>
          </CoreModules.Box>

          <CoreModules.Box sx={{ display: { md: 'flex', xs: 'none' } }}>
            <CoreModules.Button
              className='btnLogin'
              style={appBarInnerStyles.btnLogin}
              color="info"
              href="/login" >
              Login
            </CoreModules.Button>

            <CoreModules.Button
              className='btnSignUp'
              style={appBarInnerStyles.btnLogin}
              color="info"
              href="/signup">
              Sign up
            </CoreModules.Button>
          </CoreModules.Box>
          <CoreModules.Box >
            <CoreModules.IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleOpenDrawer}
              color="inherit"
            >
              <AssetModules.MenuIcon />
            </CoreModules.IconButton>
          </CoreModules.Box>
        </CoreModules.Toolbar>
      </CoreModules.AppBar>

    </CoreModules.Box>
  );
}
