import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider, Outlet } from 'react-router-dom'

import store from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";


ReactDOM.render(
  <Provider store={store}>
    <RouterProvider router={routes} />
  </Provider>
  , document.getElementById("app"));
