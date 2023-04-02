import React from "react";
import windowDimention from "../hooks/WindowDimension";
import PrimaryAppBar from "../utilities/PrimaryAppBar";
import CoreModules from "../shared/CoreModules";
import CustomizedSnackbars from "../utilities/CustomizedSnackbar";
import { CommonActions } from "../store/slices/CommonSlice";
import Loader from "../utilities/AppLoader";

const MainView = () => {
    const dispatch = CoreModules.useDispatch();
    const { windowSize } = windowDimention();
    const checkTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    const theme = CoreModules.createTheme(checkTheme)  
    const stateSnackBar = CoreModules.useSelector((state) => state.common.snackbar);
    const handleClose = (event, reason) => {
        if (reason === "clickaway") {
            return;
        }
        dispatch(
            CommonActions.SetSnackBar({
                open: false,
                message: stateSnackBar.message,
                variant: stateSnackBar.variant,
                duration: 0,
            })
        );
    };
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
                    <CoreModules.Stack sx={{ height: '100vh' }} >
                        <PrimaryAppBar />
                        <CoreModules.Stack className="mainview" sx={{ height: windowSize.width <= 599 ? '90vh' : '92vh', overflow: 'auto' }}>
                            <CoreModules.Outlet />
                            {/* Footer */}
                        </CoreModules.Stack>
                    </CoreModules.Stack>
                </CoreModules.Container>
            </CoreModules.Paper>
        </CoreModules.ThemeProvider>
    )
}

export default MainView;
