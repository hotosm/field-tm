import React from "react";
import Home from "./Home";
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import windowDimention from "../hooks/WindowDimension";
import PrimaryAppBar from "../utilities/PrimaryAppBar";
import { Outlet } from "react-router-dom";
import { ThemeProvider, CssBaseline, Paper, createTheme } from "@mui/material";
import { useSelector, useDispatch } from "react-redux";
import CustomizedSnackbar from "../utilities/CustomizedSnackbar";
import { HomeActions } from "../store/slices/HomeSlice";


const MainView = () => {
    const dispatch = useDispatch();
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
                        <Box className="mainview" sx={{ height: windowSize.width <= 599 ? '90vh' : '92vh', overflow: 'auto' }}>
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