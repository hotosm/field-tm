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

const App = () => {
  return (
    <Router>
      <div className="container-fluid p-0" >
        <div className="row">

          <div className="col-md-12">
             <PrimarySearchAppBar />
          </div>

          <div className="row">
            <SearchableRow />
          </div>

          <div className="row">
            <Drawer />
            <div className="col-md-12 p-2 content">
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                <Routes>
                  <Route path="/" element={
                      <Home />
                  } />

                </Routes>
              </div>
            </div>
          </div>

        </div>
      </div>
    </Router>
  )
}
ReactDOM.render(<App />, document.getElementById("app"));
