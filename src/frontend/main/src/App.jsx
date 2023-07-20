import React from "react";
import ReactDOM from "react-dom";
import { RouterProvider } from 'react-router-dom'
import { store, persistor } from './store/Store';
import { Provider } from "react-redux";
import routes from "./routes";
import { PersistGate } from "redux-persist/integration/react";
import "./index.css";
import 'react-loading-skeleton/dist/skeleton.css'
import * as Sentry from "@sentry/react";
import environment from "./environment";
// import 'swiper/css';
// import 'swiper/css/navigation';
// import 'swiper/css/pagination';
{
  environment.nodeEnv !== 'development' ? Sentry.init({
    dsn: environment.main_url === 'fmtm.hotosm.org' ? "https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928" : "https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928",
    integrations: [
      new Sentry.BrowserTracing({
        // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
        tracePropagationTargets: ["localhost", "https:yourserver.io/api/"],
      }),
      new Sentry.Replay(),
    ],
    // Performance Monitoring
    tracesSampleRate: 1.0, // Capture 100% of the transactions, reduce in production!
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  }) : null
};


ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>
  </Provider>
  , document.getElementById("app"));
