import React, { useState } from 'react';
import windowDimention from '@/hooks/WindowDimension';
import DrawerComponent from '@/utilities/CustomDrawer';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { LoginActions } from '@/store/slices/LoginSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { revokeCookies } from '@/utilfunctions/login';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import hotLogo from '@/assets/images/favicon.svg';
import LoginPopup from '@/components/LoginPopup';
import { useAppDispatch } from '@/types/reduxTypes';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuPortal,
} from '@/components/common/Dropdown';
import { useIsAdmin } from '@/hooks/usePermissions';
import Button from '@/components/common/Button';
import { motion } from 'motion/react';

export default function PrimaryAppBar() {
  const isAdmin = useIsAdmin();
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const pathname = location.pathname;
  const { type, windowSize } = windowDimention();

  const [open, setOpen] = useState<boolean>(false);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  const handleOnSignOut = async () => {
    setOpen(false);
    try {
      await revokeCookies();
      dispatch(LoginActions.signOut());
      dispatch(ProjectActions.clearProjects([]));
    } catch {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Failed to sign out.',
        }),
      );
    }
  };

  const navItems = [
    {
      title: 'Explore Projects',
      path: '/explore',
      active: pathname === '/explore',
      isVisible: true,
      externalLink: false,
    },
    {
      title: 'Manage Users',
      path: '/manage/user',
      active: pathname === '/manage/user',
      isVisible: isAdmin,
      externalLink: false,
    },
    { title: 'Learn', path: 'https://hotosm.github.io/field-tm', active: false, isVisible: true, externalLink: true },
    {
      title: 'Support',
      path: 'https://github.com/hotosm/field-tm/issues/',
      active: false,
      isVisible: true,
      externalLink: true,
    },
  ];

  return (
    <>
      <LoginPopup />
      <DrawerComponent
        open={open}
        onClose={() => {
          setOpen(false);
        }}
        size={windowSize}
        type={type}
        setOpen={setOpen}
      />
      <div>
        <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-px-5 fmtm-py-2 fmtm-border-y fmtm-border-grey-100">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-4 fmtm-cursor-pointer" onClick={() => navigate('/')}>
            <motion.img
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              src={hotLogo}
              alt="Field-TM Logo"
              className="fmtm-w-[4.188rem] fmtm-min-w-[4.188rem] fmtm-cursor-pointer"
            />
            <motion.h3
              initial={{ x: -50, opacity: 0, filter: 'blur(5px)' }}
              animate={{ x: 0, opacity: 1, filter: 'none' }}
              className="fmtm-text-red-medium fmtm-text-xl"
            >
              Field-TM
            </motion.h3>
          </div>
          <div className="fmtm-hidden lg:fmtm-flex fmtm-items-center fmtm-gap-8 fmtm-ml-8">
            {navItems.map((navItem) => {
              if (!navItem.isVisible) return null;
              return (
                <Link
                  to={navItem.path}
                  key={navItem.path}
                  target={navItem.externalLink ? '_blank' : undefined}
                  className={`fmtm-uppercase fmtm-button fmtm-text-grey-900 hover:fmtm-text-grey-800 fmtm-duration-200 fmtm-px-3 fmtm-pt-2 fmtm-pb-1 ${
                    navItem.active ? 'fmtm-border-red-medium' : 'fmtm-border-white'
                  } fmtm-border-b-2`}
                >
                  {navItem.title}
                </Link>
              );
            })}
          </div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            {authDetails ? (
              <>
                <DropdownMenu modal={false}>
                  <DropdownMenuTrigger className="fmtm-outline-none fmtm-w-fit">
                    {authDetails.picture ? (
                      <img
                        src={authDetails.picture}
                        alt="Profile Picture"
                        className="fmtm-w-[2.25rem] fmtm-h-[2.25rem] fmtm-rounded-full fmtm-cursor-pointer"
                      />
                    ) : (
                      <div className="fmtm-w-[2.25rem] fmtm-h-[2.25rem] fmtm-rounded-full fmtm-bg-grey-600 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-cursor-pointer">
                        <h5 className="fmtm-text-white">{authDetails.username[0]?.toUpperCase()}</h5>
                      </div>
                    )}
                  </DropdownMenuTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuContent
                      className="fmtm-px-0 fmtm-py-2 fmtm-border-none fmtm-bg-white !fmtm-min-w-[17.5rem] !fmtm-shadow-[0px_0px_20px_4px_rgba(0,0,0,0.12)]"
                      align="end"
                    >
                      <div className="fmtm-flex fmtm-py-2 fmtm-px-3 fmtm-gap-3 fmtm-items-center fmtm-border-b fmtm-border-b-gray-300">
                        {authDetails.picture ? (
                          <img
                            src={authDetails.picture}
                            alt="Profile Picture"
                            className="fmtm-w-[2.25rem] fmtm-h-[2.25rem] fmtm-rounded-full fmtm-cursor-pointer"
                          />
                        ) : (
                          <div className="fmtm-w-[2.25rem] fmtm-h-[2.25rem] fmtm-rounded-full fmtm-bg-grey-600 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-cursor-pointer">
                            <h5 className="fmtm-text-white">{authDetails.username[0]?.toUpperCase()}</h5>
                          </div>
                        )}
                        <div className="fmtm-flex fmtm-flex-col">
                          <h5>{authDetails.username}</h5>
                          <p className="fmtm-body-md">{authDetails.role}</p>
                        </div>
                      </div>
                      <div>
                        <div
                          onClick={handleOnSignOut}
                          className="fmtm-flex fmtm-px-3 fmtm-py-2 fmtm-gap-2 fmtm-text-red-medium hover:fmtm-bg-red-light fmtm-cursor-pointer fmtm-duration-200"
                        >
                          <AssetModules.LogoutOutlinedIcon />
                          <p>Sign Out</p>
                        </div>
                      </div>
                    </DropdownMenuContent>
                  </DropdownMenuPortal>
                </DropdownMenu>
              </>
            ) : (
              <Button variant="secondary-red" onClick={() => dispatch(LoginActions.setLoginModalOpen(true))}>
                Login
              </Button>
            )}
            <div
              onClick={() => {
                setOpen(true);
              }}
              className="fmtm-rounded-full hover:fmtm-bg-grey-100 fmtm-cursor-pointer fmtm-duration-200 fmtm-w-9 fmtm-h-9 fmtm-flex fmtm-items-center fmtm-justify-center"
            >
              <AssetModules.MenuIcon className="fmtm-rounded-full fmtm-text-grey-800 !fmtm-text-[20px]" />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
