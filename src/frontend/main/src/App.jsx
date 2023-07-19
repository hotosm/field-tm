import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider } from 'react-router-dom'
import { store, persistor } from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";
import { PersistGate } from "redux-persist/integration/react";
import "./index.css";
import 'react-loading-skeleton/dist/skeleton.css'
import * as Sentry from "@sentry/browser";
import environment from "./environment";
// import 'swiper/css';
// import 'swiper/css/navigation';
// import 'swiper/css/pagination';
{ environment.nodeEnv !== 'development' ? Sentry.init({ dsn: environment.main_url === 'fmtm.hotosm.org' ? "https://419f6e226571489d9a767f75c7ae157f@glitchtip.naxa.com.np/6" : "https://2f6079201d4a48f8acdb1a31763e0c0d@glitchtip.naxa.com.np/4" }) : null };


ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>
  </Provider>
  , document.getElementById("app"));
