import React, { Suspense } from "react";
import WindowDimension from "fmtm/WindowDimension";
import CoreModules from 'fmtm/CoreModules';
export default function MainView() {

    const { windowSize } = WindowDimension();
    const getTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    const theme = CoreModules.createTheme(getTheme)
    const PrimaryAppBar = React.lazy(() => import('fmtm/PrimaryAppBar'))
    return (
        <CoreModules.ThemeProvider theme={theme}>
            <CoreModules.CssBaseline />
            <CoreModules.Paper>
                <CoreModules.Container disableGutters={true} maxWidth={false}>

                    <CoreModules.Box sx={{ height: '100vh' }} >
                        <Suspense fallback={<div></div>}>
                            <PrimaryAppBar />
                        </Suspense>
                        <CoreModules.Box sx={{ height: windowSize.width <= 599 ? '90vh' : '92vh' }}>
                            <CoreModules.Outlet />
                            {/* Footer */}
                        </CoreModules.Box>
                    </CoreModules.Box>
                </CoreModules.Container>
            </CoreModules.Paper>
        </CoreModules.ThemeProvider>
    )
}
