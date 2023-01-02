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
import './fonts/Rouphen/Roughpen-8M2q2.ttf';
import './fonts/RoyalLodge/RoyalLodge-vm7P4.otf'
import './fonts/Bicycle/BicycleTrack-PK4RZ.otf'
import './fonts/Raimei/RaimeiHakke-2O5ye.otf'
import './fonts/CheesyBread/CheesyBread-DOgRW.ttf'
import './fonts/OldFive/OldEnglishFive.ttf'

const App = () => {
  return (
    <Router>
      <Container disableGutters={true} maxWidth={false} >
        <Box sx={{ bgcolor: 'white', height: '100vh' }} >
          <PrimarySearchAppBar />
          <SearchableRow />
          <Box sx={{ height: '76vh', overflow: 'auto' }}>
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
