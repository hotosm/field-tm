import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider } from 'react-router-dom'
import { store, persistor } from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";
import { PersistGate } from "redux-persist/integration/react";
import "./index.css";

import 'react-loading-skeleton/dist/skeleton.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'rsuite/dist/rsuite.min.css'
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';
ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>

  </Provider>
  , document.getElementById("app"));
