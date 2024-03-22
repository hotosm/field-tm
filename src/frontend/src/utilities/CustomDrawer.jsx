import React, { useEffect, useState } from 'react';
import SwipeableDrawer from '@mui/material/SwipeableDrawer';
import Button from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { NavLink } from 'react-router-dom';
import { createLoginWindow, revokeCookie } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';
import { LoginActions } from '@/store/slices/LoginSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';

export default function CustomDrawer({ open, placement, size, type, onClose, onSignOut, setOpen }) {
  const [showDebugConsole, setShowDebugConsole] = useState(false);
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    if (import.meta.env.MODE === 'development') {
      // Override console.log to capture logs
      const originalConsoleLog = console.log;
      console.log = (...args) => {
        originalConsoleLog.apply(console, args);
        setLogs((prevLogs) => [
          ...prevLogs,
          args.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : arg)).join(' '),
        ]);
      };

      // Restore original console.log when component unmounts
      return () => {
        console.log = originalConsoleLog;
      };
    }
  }, []);
  const toggleDebugConsole = () => {
    setShowDebugConsole((prev) => !prev);
  };

  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const dispatch = CoreModules.useAppDispatch();

  const onMouseEnter = (event) => {
    const element = document.getElementById(`text${event.target.id}`);
    element != null ? (element.style.color = `${defaultTheme.palette.error['main']}`) : null;
  };
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const onMouseLeave = (event) => {
    const element = document.getElementById(`text${event.target.id}`);
    element != null ? (element.style.color = `${defaultTheme.palette.info['main']}`) : null;
  };
  const Drawerstyles = {
    list: {
      width: type == 'xs' ? size.width - 48 : type == 'sm' ? size.width - 48 : 350,
    },
    outlineBtn: {
      padding: 8,
      width: '100%',
      marginTop: '4%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily,
    },
    containedBtn: {
      padding: 8,
      width: '100%',
      marginTop: '0.7%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily,
    },
  };

  const MenuItems = [
    {
      name: 'Explore Projects',
      ref: '/',
      isExternalLink: false,
      isActive: true,
    },
    {
      name: 'Manage Organizations',
      ref: '/organisation',
      isExternalLink: false,
      isActive: true,
    },
    {
      name: 'Manage Category',
      ref: '/',
      isExternalLink: false,
      isActive: true,
    },
    {
      name: 'My Contributions',
      ref: 'TBD',
      isExternalLink: false,
      isActive: false,
    },
    {
      name: 'Learn',
      ref: 'https://hotosm.github.io/fmtm',
      isExternalLink: true,
      isActive: true,
    },
    {
      name: 'About',
      ref: 'https://hotosm.github.io/fmtm/About/',
      isExternalLink: true,
      isActive: true,
    },
    {
      name: 'Support',
      ref: 'https://github.com/hotosm/fmtm/issues/',
      isExternalLink: true,
      isActive: true,
    },
  ];

  const handleOnSignOut = async () => {
    setOpen(false);
    try {
      await revokeCookie();
      dispatch(LoginActions.signOut(null));
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

  return (
    <div>
      {import.meta.env.MODE === 'development' && (
        <div>
          <div
            style={{
              position: 'fixed',
              bottom: 0,
              width: '100%',
              height: '33vh',
              backgroundColor: 'white',
              border: '1px solid',
              padding: '16px 32px',
              display: showDebugConsole ? 'flex' : 'none',
              flexDirection: 'column',
              zIndex: 10000,
              overflowY: 'auto',
            }}
          >
            <button style={{ alignSelf: 'flex-end', marginBottom: '10px' }} onClick={toggleDebugConsole}>
              Close
            </button>
            {/* Display console logs */}
            {logs.map((log, index) => (
              <p key={index}>{log}</p>
            ))}
          </div>
        </div>
      )}
      <React.Fragment>
        <SwipeableDrawer swipeAreaWidth={0} onOpen={onClose} anchor={'right'} open={open} onClose={onClose}>
          <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', padding: 3 }}>
            <CoreModules.Stack sx={{ width: 50, borderRadius: '50%', marginLeft: '0.7%' }}>
              <CoreModules.IconButton
                size="large"
                aria-label="show more"
                aria-haspopup="true"
                onClick={onClose}
                color="info"
              >
                <AssetModules.CloseIcon />
              </CoreModules.IconButton>
            </CoreModules.Stack>

            <CoreModules.Divider color={'info'} sx={{ display: { xs: 'block', md: 'none' } }} />
            {token != null && (
              <CoreModules.Stack
                direction={'row'}
                className="fmtm-justify-center fmtm-items-center fmtm-my-2"
                ml={'3%'}
                spacing={1}
              >
                {token['picture'] !== 'null' && token['picture'] ? (
                  <CoreModules.Stack
                    className="fmtm-w-7 fmtm-h-7 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-overflow-hidden fmtm-rounded-full fmtm-border-[1px]"
                    sx={{ display: { xs: 'block', md: 'none' }, mt: '3%' }}
                  >
                    <img src={token['picture']} alt="Profile Picture" />
                  </CoreModules.Stack>
                ) : (
                  <AssetModules.PersonIcon color="success" sx={{ display: { xs: 'block', md: 'none' }, mt: '1%' }} />
                )}
                <CoreModules.Typography
                  variant="subtitle2"
                  color={'info'}
                  noWrap
                  sx={{ display: { xs: 'block', md: 'none' } }}
                  className="fmtm-w-fit"
                >
                  {token['username']}
                </CoreModules.Typography>
              </CoreModules.Stack>
            )}
            <CoreModules.Divider color={'info'} sx={{ display: { xs: 'block', md: 'none' } }} />
            <CoreModules.List sx={Drawerstyles.list} component="nav" aria-label="mailStack folders">
              {MenuItems.filter((menuItem) => menuItem.isActive).map((menuDetails, index) =>
                menuDetails.isExternalLink ? (
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    key={index}
                    href={menuDetails.ref}
                    style={{
                      textDecoration: 'inherit',
                      color: 'inherit',
                      fontFamily: 'inherit',
                      fontWeight: 400,
                      fontSize: '1.01587rem',
                      background: '#000000',
                      opacity: 0.8,
                    }}
                  >
                    <CoreModules.ListItem
                      id={index.toString()}
                      onMouseEnter={onMouseEnter}
                      onMouseLeave={onMouseLeave}
                      key={index}
                    >
                      <CoreModules.ListItemText id={`text${index}`} primary={menuDetails.name} />
                    </CoreModules.ListItem>
                  </a>
                ) : (
                  <NavLink
                    key={index}
                    to={menuDetails.ref}
                    className={`fmtm-no-underline fmtm-text-inherit fmtm-opacity-80 ${
                      menuDetails.name === 'Explore Projects' || menuDetails.name === 'Manage Organizations'
                        ? 'lg:fmtm-hidden'
                        : ''
                    }`}
                  >
                    <CoreModules.ListItem
                      id={index.toString()}
                      onMouseEnter={onMouseEnter}
                      onMouseLeave={onMouseLeave}
                      key={index}
                    >
                      <CoreModules.ListItemText id={`text${index}`} primary={menuDetails.name} />
                    </CoreModules.ListItem>
                  </NavLink>
                ),
              )}
              {import.meta.env.MODE === 'development' && (
                <Button onClick={() => setShowDebugConsole(true)} btnText="Open Console" btnType="secondary" />
              )}
              <div className="fmtm-ml-4 fmtm-mt-2 lg:fmtm-hidden">
                {token != null ? (
                  <div
                    className="fmtm-text-[#d73e3e] hover:fmtm-text-[#d73e3e] fmtm-cursor-pointer fmtm-opacity-80"
                    onClick={handleOnSignOut}
                  >
                    Sign Out
                  </div>
                ) : (
                  <div
                    className="fmtm-text-[#44546a] hover:fmtm-text-[#d73e3e] fmtm-cursor-pointer fmtm-opacity-80"
                    onClick={() => createLoginWindow('/')}
                  >
                    Sign In
                  </div>
                )}
              </div>
            </CoreModules.List>
          </CoreModules.Stack>
        </SwipeableDrawer>
      </React.Fragment>
    </div>
  );
}
