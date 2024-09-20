import React, { useState } from 'react';
import SwipeableDrawer from '@mui/material/SwipeableDrawer';
import Button from '@/components/common/Button';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { NavLink } from 'react-router-dom';
import { revokeCookie } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';
import { LoginActions } from '@/store/slices/LoginSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import DebugConsole from '@/utilities/DebugConsole';
import { useAppSelector } from '@/types/reduxTypes';

type customDrawerType = {
  open: boolean;
  size: { width: number; height: number };
  type: string;
  onClose: () => void;
  setOpen: (open: boolean) => void;
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
    ref: 'https://docs.fmtm.dev/About/',
    isExternalLink: true,
    isActive: true,
  },
  {
    name: 'Support',
    ref: 'https://github.com/hotosm/fmtm/issues/',
    isExternalLink: true,
    isActive: true,
  },
  {
    name: 'Download Custom ODK Collect',
    ref: 'https://github.com/hotosm/odkcollect/releases/download/v2024.2.4-entity-select/ODK-Collect-v2024.2.4-entity-select.apk',
    isExternalLink: true,
    isActive: true,
  },
];

export default function CustomDrawer({ open, size, type, onClose, setOpen }: customDrawerType) {
  const dispatch = CoreModules.useAppDispatch();

  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const [showDebugConsole, setShowDebugConsole] = useState(false);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  const onMouseEnter = (event: React.MouseEvent<HTMLElement>) => {
    const targetElement = event.target as HTMLElement;
    const element = document.getElementById(`text${targetElement.id}`);
    if (element) element.style.color = defaultTheme.palette.error.main;
  };

  const onMouseLeave = (event: React.MouseEvent<HTMLElement>) => {
    const targetElement = event.target as HTMLElement;
    const element = document.getElementById(`text${targetElement.id}`);
    if (element) element.style.color = defaultTheme.palette.info.main;
  };

  const Drawerstyles = {
    list: {
      width: type === 'xs' || type === 'sm' ? size.width - 48 : 350,
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

  return (
    <div>
      <DebugConsole showDebugConsole={showDebugConsole} setShowDebugConsole={setShowDebugConsole} />
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
            {authDetails && (
              <CoreModules.Stack
                direction={'row'}
                className="fmtm-justify-center fmtm-items-center fmtm-my-2"
                ml={'3%'}
                spacing={1}
              >
                {authDetails['profile_img'] !== 'null' && authDetails['profile_img'] ? (
                  <CoreModules.Stack
                    className="fmtm-w-7 fmtm-h-7 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-overflow-hidden fmtm-rounded-full fmtm-border-[1px]"
                    sx={{ display: { xs: 'block', md: 'none' }, mt: '3%' }}
                  >
                    <img src={authDetails['profile_img']} alt="Profile Picture" />
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
                  {authDetails['username']}
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
                {authDetails ? (
                  <div
                    className="fmtm-text-[#d73e3e] hover:fmtm-text-[#d73e3e] fmtm-cursor-pointer fmtm-opacity-80"
                    onClick={handleOnSignOut}
                  >
                    Sign Out
                  </div>
                ) : (
                  <div
                    className="fmtm-text-[#44546a] hover:fmtm-text-[#d73e3e] fmtm-cursor-pointer fmtm-opacity-80"
                    onClick={() => {
                      onClose();
                      dispatch(LoginActions.setLoginModalOpen(true));
                    }}
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
