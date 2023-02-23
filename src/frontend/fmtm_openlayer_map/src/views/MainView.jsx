import React from "react";
import {useSelector} from 'react-redux'
import { Box, Container, createTheme, CssBaseline, Paper, ThemeProvider } from "@mui/material";
import { Outlet } from "react-router-dom";
import PrimaryAppBar from 'fmtm/PrimaryAppBar'
import WindowDimension from "fmtm/WindowDimension";
export default function MainView() {

     const {windowSize} = WindowDimension();
     const getTheme = useSelector(state => state.theme.hotTheme)
     const theme = createTheme(getTheme)

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Paper>
                <Container disableGutters={true} maxWidth={false}>
                    <Box sx={{ height: '100vh' }} >
                        <PrimaryAppBar />
                        <Box sx={{ height: windowSize.width <= 599 ? '90vh' : '92vh', overflow: 'auto' }}>
                            <Outlet />
                            {/* Footer */}
                        </Box>
                    </Box>
                </Container>
            </Paper>
        </ThemeProvider>
    )
}