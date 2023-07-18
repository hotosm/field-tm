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
// { environment.nodeEnv !== 'development' ? Sentry.init({ dsn: "https://42207adea3754eab8f1828ed0466d1d8@glitchtip.naxa.com.np/1" }) : null };
Sentry.init({ dsn: "https://2f6079201d4a48f8acdb1a31763e0c0d@glitchtip.naxa.com.np/4" });

ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>
  </Provider>
  , document.getElementById("app"));
