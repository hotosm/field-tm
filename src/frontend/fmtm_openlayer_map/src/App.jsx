
import React, { useEffect, useState } from "react";
import './index.css'
import ReactDOM from "react-dom";
import { persistor, store } from "./store/store";
import { Provider, useDispatch, useSelector } from "react-redux";
import { PersistGate } from 'redux-persist/integration/react';
import routes from "./routes";
import { RouterProvider } from "react-router-dom";

ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>
  </Provider>
  ,
  document.getElementById("app")
);
