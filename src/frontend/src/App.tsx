import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider, Outlet } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles';
import store from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";
import "./index.css";
import './assets/fonts/Barlow/Barlow-Bold.ttf';
import './assets/fonts/Barlow/Barlow-Medium.ttf'
import './assets/fonts/Archivo/Archivo/Archivo-Bold.ttf'
import './assets/fonts/Archivo/Archivo/Archivo-Regular.ttf'
import './assets/fonts/Archivo/Archivo/Archivo-Medium.ttf'
import './assets/fonts/Archivo/Archivo/Archivo-Medium.ttf'
import './assets/fonts/Archivo/Archivo/Archivo-Light.ttf'
import 'react-loading-skeleton/dist/skeleton.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'rsuite/dist/rsuite.min.css'
import 'leaflet/dist/leaflet.css';
// import Swiper and modules styles
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';

ReactDOM.render(
  <Provider store={store}>
    <RouterProvider router={routes} />
  </Provider>
  , document.getElementById("app"));
