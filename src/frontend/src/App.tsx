import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'rsuite/dist/rsuite.min.css'
import PrimarySearchAppBar from "./utilities/AppBar";
import Drawer from "./utilities/Drawer";
import DrawerToggler from "./components/DrawerToggler";
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import Home from "./pages/Home";
import SearchableRow from "./utilities/SearchableRow";
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
const App = () => {
  return (
    <Router>
      <Container disableGutters={true} maxWidth={false} >
        <Drawer />
        <Box sx={{ bgcolor: 'whitesmoke', height: '100vh' }} >
          <PrimarySearchAppBar />
          <SearchableRow />
          <Box sx={{ height: '84vh', overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<Home />} />
            </Routes>
          </Box>
        </Box>
      </Container>
    </Router>
  )
}
ReactDOM.render(<App />, document.getElementById("app"));
