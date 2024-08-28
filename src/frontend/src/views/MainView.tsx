import React, { useEffect } from 'react';
import windowDimention from '@/hooks/WindowDimension';
import PrimaryAppBar from '@/utilities/PrimaryAppBar';
import CoreModules from '@/shared/CoreModules';
import CustomizedSnackbars from '@/utilities/CustomizedSnackbar';
import { CommonActions } from '@/store/slices/CommonSlice';
import Loader from '@/utilities/AppLoader';
import MappingHeader from '@/utilities/MappingHeader';
import { useLocation, useSearchParams } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import ProjectNotFound from './ProjectNotFound';

const MainView = () => {
  const dispatch = CoreModules.useAppDispatch();
  const { pathname } = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { windowSize } = windowDimention();
  const checkTheme = useAppSelector((state) => state.theme.hotTheme);
  const theme = CoreModules.createTheme(checkTheme);
  const stateSnackBar = useAppSelector((state) => state.common.snackbar);
  const projectNotFound = useAppSelector((state) => state.common.projectNotFound);

  const handleClose = (event: React.SyntheticEvent, reason: string) => {
    if (reason === 'clickaway') {
      return;
    }
    dispatch(
      CommonActions.SetSnackBar({
        open: false,
        message: stateSnackBar.message,
        variant: stateSnackBar.variant,
        duration: 0,
      }),
    );
  };

  const popupInParams = searchParams.get('popup');

  useEffect(() => {
    if (!projectNotFound) return;
    dispatch(CommonActions.SetProjectNotFound(false));
  }, [pathname]);

  return (
    <CoreModules.ThemeProvider theme={theme}>
      <CustomizedSnackbars
        duration={stateSnackBar.duration}
        open={stateSnackBar.open}
        variant={stateSnackBar.variant}
        message={stateSnackBar.message}
        handleClose={handleClose}
      />
      <CoreModules.CssBaseline />
      <Loader />
      <CoreModules.Paper>
        <CoreModules.Container disableGutters={true} maxWidth={false}>
          <CoreModules.Stack sx={{ height: '100vh' }}>
            {popupInParams === 'true' || (pathname.includes('/project/') && windowSize.width <= 640) ? (
              <div></div>
            ) : (
              <div>
                <MappingHeader />
                <PrimaryAppBar />
              </div>
            )}
            {projectNotFound ? (
              <ProjectNotFound />
            ) : (
              <CoreModules.Stack
                className={`${
                  pathname.includes('/project/') && windowSize.width < 640 ? '' : 'fmtm-p-6'
                } fmtm-bg-[#f5f5f5]`}
                sx={{
                  height: popupInParams
                    ? '100vh'
                    : pathname.includes('project/') && windowSize.width <= 640
                      ? '100vh'
                      : windowSize.width <= 599
                        ? '90vh'
                        : '92vh',
                  overflow: 'auto',
                  // p: '1.3rem',
                }}
              >
                <CoreModules.Outlet />
                {/* Footer */}
              </CoreModules.Stack>
            )}
          </CoreModules.Stack>
        </CoreModules.Container>
      </CoreModules.Paper>
    </CoreModules.ThemeProvider>
  );
};

export default MainView;
