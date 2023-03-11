import React from "react";
import { useSelector } from 'react-redux'
import PrimaryAppBar from 'fmtm/PrimaryAppBar'
import WindowDimension from "fmtm/WindowDimension";
import CoreModules from 'fmtm/CoreModules';
export default function MainView() {

    const { windowSize } = WindowDimension();
    const getTheme = useSelector(state => state.theme.hotTheme)
    const theme = CoreModules.createTheme(getTheme)

    return (
        <CoreModules.ThemeProvider theme={theme}>
            <CoreModules.CssBaseline />
            <CoreModules.Paper>
                <CoreModules.Container disableGutters={true} maxWidth={false}>

                    <CoreModules.Box sx={{ height: '100vh' }} >
                        <PrimaryAppBar />
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