import React from "react";
import windowDimention from "../hooks/WindowDimension";
import PrimaryAppBar from "../utilities/PrimaryAppBar";
import CoreModules from "../shared/CoreModules";

const MainView = () => {
    const dispatch = CoreModules.useDispatch();
    const { windowSize } = windowDimention();
    const checkTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    const theme = CoreModules.createTheme(checkTheme)
    return (
        <CoreModules.ThemeProvider theme={theme}>
            <CoreModules.CssBaseline />
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
