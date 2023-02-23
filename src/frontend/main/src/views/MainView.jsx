import React from "react";
import Home from "./Home";
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import windowDimention from "../hooks/WindowDimension";
import PrimaryAppBar from "../utilities/PrimaryAppBar";
import { Outlet } from "react-router-dom";
import { ThemeProvider, CssBaseline, Paper, createTheme } from "@mui/material";
import { useSelector } from "react-redux";


const MainView = () => {
    const { windowSize } = windowDimention();
    const checkTheme = useSelector(state => state.theme.hotTheme)
    const theme = createTheme(checkTheme)
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

export default MainView;