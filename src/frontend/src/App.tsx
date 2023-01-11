import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import Home from "./pages/Home";
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import windowDimention from "./customHooks/WindowDimension";
import PrimaryAppBar from "./utilities/PrimaryAppBar";
import SearchablesRow from "./components/home/SearchablesRow";
import store from './store/Store';
import { Provider } from "react-redux";
import ProjectDetails from "./pages/ProjectDetails";



const App = () => {
  const { windowSize, type } = windowDimention();

  return (
    <Router>
      <Container disableGutters={true} maxWidth={false} >
        <Box sx={{ bgcolor: 'white', height: '100vh' }} >
          <PrimaryAppBar />
          <Box sx={{ height: windowSize.width <= 599 ? '73vh' : '76vh', overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/project_details" element={<ProjectDetails />} />
            </Routes>
          </Box>
        </Box>
      </Container>
    </Router>
  )
}
ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>
  , document.getElementById("app"));
