import axios from 'axios';
import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import { RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';

import { store, persistor } from '@/store/Store';
import routes from '@/routes';
import environment from '@/environment';

import '@/index.css';
import 'ol/ol.css';
import 'react-loading-skeleton/dist/skeleton.css';

// Added Fix of Console Error of MUI Issue
const consoleError = console.error;
const SUPPRESSED_WARNINGS = [
  'MUI: The `value` provided to the Tabs component is invalid.',
  'React does not recognize the `%s` prop on a DOM element. If you intentionally want it to appear in the DOM as a custom attribute, spell it as lowercase `%s` instead.',
  'Using kebab-case for css properties in objects is not supported. Did you mean WebkitBoxOrient?',
  'Using kebab-case for css properties in objects is not supported. Did you mean WebkitLineClamp?',
  'If you used to conditionally omit it with %s={condition && value}, pass %s={condition ? value : undefined} instead.%s',
];

console.error = function filterWarnings(msg, ...args) {
  if (!SUPPRESSED_WARNINGS.some((entry) => msg.includes(entry))) {
    consoleError(msg, ...args);
  }
};
axios.interceptors.request.use(
  (config) => {
    // Do something before request is sent

    // const excludedDomains = ['xxx', 'xxx'];
    // const urlIsExcluded = excludedDomains.some((domain) => config.url.includes(domain));
    // if (!urlIsExcluded) {
    //   config.withCredentials = true;
    // }

    config.withCredentials = true;

    return config;
  },
  (error) =>
    // Do something with request error
    Promise.reject(error),
);
const GlobalInit = () => {
  useEffect(() => {
    console.log('adding interceptors');
    axios.interceptors.request.use(
      (config) => {
        // Do something before request is sent

        // const excludedDomains = ['xxx', 'xxx'];
        // const urlIsExcluded = excludedDomains.some((domain) => config.url.includes(domain));
        // if (!urlIsExcluded) {
        //   config.withCredentials = true;
        // }

        config.withCredentials = true;

        return config;
      },
      (error) =>
        // Do something with request error
        Promise.reject(error),
    );
    return () => {};
  }, []);

  return null; // Renders nothing
};

const SentryInit = () => {
  useEffect(() => {
    if (import.meta.env.MODE === 'development') {
      return;
    }
    console.log('Adding Sentry');

    import('@sentry/react').then((Sentry) => {
      // Init Sentry
      Sentry.init({
        dsn:
          import.meta.env.BASE_URL === 'fmtm.hotosm.org'
            ? 'https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928'
            : 'https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928',
        integrations: [
          new Sentry.BrowserTracing({
            // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
            tracePropagationTargets: ['https://fmtm.naxa.com.np/', 'https://fmtm.hotosm.org/'],
          }),
          new Sentry.Replay(),
        ],
        // Performance Monitoring
        tracesSampleRate: 1.0, // Capture 100% of the transactions, reduce in production!
        // Session Replay
        replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
        replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
      });
    });

    return () => {};
  }, []);

  return null; // Renders nothing
};

// Matomo Tracking Component
const MatomoTrackingInit = () => {
  useEffect(() => {
    if (import.meta.env.MODE === 'development' || import.meta.env.BASE_URL !== 'fmtm.hotosm.org') {
      return;
    }
    // Set matomo tracking id
    window.site_id = environment.matomoTrackingId;

    // Create optout-form div for banner
    const optoutDiv = document.createElement('div');
    optoutDiv.id = 'optout-form'; // Set an ID if needed
    document.body.appendChild(optoutDiv);

    // Load CDN script
    const script = document.createElement('script');
    script.src = 'https://cdn.hotosm.org/tracking-v3.js';
    document.body.appendChild(script);
    // Manually trigger DOMContentLoaded, that script hooks
    // https://github.com/hotosm/matomo-tracking/blob/9b95230cb5f0bf2a902f00379152f3af9204c641/tracking-v3.js#L125
    script.onload = () => {
      optoutDiv.dispatchEvent(
        new Event('DOMContentLoaded', {
          bubbles: true,
          cancelable: true,
        }),
      );
    };

    // Cleanup on unmount
    return () => {
      document.body.removeChild(optoutDiv);
      document.body.removeChild(script);
    };
  }, []);

  return null; // Renders nothing
};

// The main App render
ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <GlobalInit />
      <RouterProvider router={routes} />
      <MatomoTrackingInit />
      <SentryInit />
    </PersistGate>
  </Provider>,
  document.getElementById('app'),
);

// Register service worker
if (import.meta.env.MODE === 'production') {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/service-worker.js')
        .then((registration) => {
          console.log('ServiceWorker registered: ', registration);
        })
        .catch((error) => {
          console.log('ServiceWorker registration failed: ', error);
        });
    });
  }
}
// if (import.meta.env.MODE === 'development') {
//   navigator.serviceWorker.getRegistrations().then(function (registrations) {
//     for (let registration of registrations) {
//       registration.unregister();
//     }
//   });
// }
