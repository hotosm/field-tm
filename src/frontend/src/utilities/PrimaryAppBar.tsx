import * as React from 'react';
import windowDimention from '@/hooks/WindowDimension';
import DrawerComponent from '@/utilities/CustomDrawer';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { LoginActions } from '@/store/slices/LoginSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { revokeCookie } from '@/utilfunctions/login';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import logo from '@/assets/images/hotLog.png';
import LoginPopup from '@/components/LoginPopup';

export default function PrimaryAppBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = React.useState<boolean>(false);
  const dispatch = CoreModules.useAppDispatch();
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const handleOpenDrawer = () => {
    setOpen(true);
  };

  const handleOnCloseDrawer = () => {
    setOpen(false);
  };

  React.useEffect(() => {
    if (location.pathname.includes('organisation') || location.pathname.includes('organization')) {
      setActiveTab(1);
    } else {
      setActiveTab(0);
    }
  }, [location]);

  const appBarInnerStyles = {
    logo: {
      width: 111,
      height: 32,
    },
    btnLogin: {
      fontSize: defaultTheme.typography.h3.fontSize,
    },
  };

  const handleOnSignOut = async () => {
    setOpen(false);
    try {
      await revokeCookie();
      dispatch(LoginActions.signOut());
      dispatch(ProjectActions.clearProjects([]));
    } catch {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Failed to sign out.',
          variant: 'error',
          duration: 2000,
        }),
      );
    }
  };

  const { type, windowSize } = windowDimention();

  const [activeTab, setActiveTab] = useState(0);

  return (
    <CoreModules.Stack sx={{ flexGrow: 0 }}>
      <LoginPopup />
      <DrawerComponent
        open={open}
        placement={'right'}
        onClose={handleOnCloseDrawer}
        size={windowSize}
        type={type}
        onSignOut={handleOnSignOut}
        setOpen={setOpen}
      />
      <CoreModules.AppBar
        position="static"
        sx={{ boxShadow: 0, borderBottom: '1px solid #e1e0e0', borderTop: '1px solid #e1e0e0' }}
      >
        <CoreModules.Toolbar>
          <img src={logo} alt="FMTM Logo" onClick={() => navigate('/')} className="fmtm-w-[5.5rem] sm:fmtm-w-28" />

          {/* Tabs switch added */}
          <CoreModules.Tabs
            sx={{
              marginLeft: '2%',
              flexGrow: 20,
              display: {
                xs: 'none',
                sm: 'none',
                md: 'block',
                lg: 'block',
              },
            }}
            className="header-tabs"
          >
            <CoreModules.Link to={'/'} style={{ color: defaultTheme.palette.black }}>
              <CoreModules.Tab
                label="EXPLORE PROJECTS"
                sx={{
                  borderBottom: activeTab === 0 ? '2.5px solid #2c3038' : 'none',
                  '&:hover': { backgroundColor: '#ffff' },
                  fontSize: 16,
                }}
                onClick={() => setActiveTab(0)}
              />
            </CoreModules.Link>
            <CoreModules.Link to={'/organisation'} style={{ color: defaultTheme.palette.black }}>
              <CoreModules.Tab
                label="MANAGE ORGANIZATIONS"
                sx={{
                  borderBottom: activeTab === 1 ? '2.5px solid #2c3038' : 'none',
                  '&:hover': { backgroundColor: '#fff' },
                  fontSize: 16,
                }}
                onClick={() => setActiveTab(1)}
              />
            </CoreModules.Link>
          </CoreModules.Tabs>
          <CoreModules.Stack sx={{ flexGrow: 1 }} />

          {/* position changed */}
          {authDetails && (
            <CoreModules.Stack
              direction={'row'}
              spacing={1}
              justifyContent="end"
              alignItems="center"
              className="fmtm-text-ellipsis fmtm-max-w-[9.5rem]"
            >
              {authDetails['img_url'] !== 'null' && authDetails['img_url'] ? (
                <CoreModules.Stack
                  className="fmtm-w-7 fmtm-h-7 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-overflow-hidden fmtm-rounded-full fmtm-border-[1px]"
                  sx={{ display: { xs: 'none', md: 'block' }, mt: '3%' }}
                >
                  <img src={authDetails['img_url']} alt="Profile Picture" />
                </CoreModules.Stack>
              ) : (
                <AssetModules.PersonIcon color="success" sx={{ mt: '3%' }} />
              )}
              <CoreModules.Typography variant="typography" color={'info'} noWrap>
                {authDetails['username']}
              </CoreModules.Typography>
            </CoreModules.Stack>
          )}

          <CoreModules.Stack direction={'row'} sx={{ display: { md: 'flex' } }}>
            {authDetails ? (
              <CoreModules.Link style={{ textDecoration: 'none' }} className="fmtm-hidden sm:fmtm-flex" to={'/'}>
                <CoreModules.Button
                  className="btnLogin fmtm-truncate"
                  style={appBarInnerStyles.btnLogin}
                  color="error"
                  onClick={handleOnSignOut}
                >
                  Sign Out
                </CoreModules.Button>
              </CoreModules.Link>
            ) : (
              <CoreModules.Button
                className="btnLogin fmtm-truncate"
                style={appBarInnerStyles.btnLogin}
                color="info"
                onClick={() => dispatch(LoginActions.setLoginModalOpen(true))}
              >
                Sign in
              </CoreModules.Button>
            )}
          </CoreModules.Stack>
          <CoreModules.Stack>
            <CoreModules.IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={handleOpenDrawer}
              color="inherit"
            >
              <AssetModules.MenuIcon />
            </CoreModules.IconButton>
          </CoreModules.Stack>
        </CoreModules.Toolbar>
      </CoreModules.AppBar>
    </CoreModules.Stack>
  );
}
