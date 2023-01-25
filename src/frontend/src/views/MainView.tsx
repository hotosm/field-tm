import React from "react";
import Home from "./Home";
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import windowDimention from "../hooks/WindowDimension";
import PrimaryAppBar from "../utilities/PrimaryAppBar";
import { Outlet } from "react-router-dom";



const MainView = () => {
    const { windowSize, type } = windowDimention();

    return (
        <Container disableGutters={true} maxWidth={false}>
            <Box sx={{ bgcolor: 'white', height: '100vh' }} >
                <PrimaryAppBar />
                <Box sx={{ height: windowSize.width <= 599 ? '90vh' : '92vh', overflow: 'auto' }}>
                    <Outlet />
                    {/* Footer */}
                </Box>
            </Box>
        </Container>
    )
}

export default MainView;