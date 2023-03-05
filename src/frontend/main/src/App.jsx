import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider } from 'react-router-dom'
import {store,persistor} from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";
import { PersistGate } from "redux-persist/integration/react";
 
ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>

  </Provider>
  , document.getElementById("app"));
