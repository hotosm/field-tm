import React from 'react';
import ReactDOM from 'react-dom';
import { RouterProvider } from 'react-router-dom';
import { store, persistor } from './store/Store';
import { Provider } from 'react-redux';
import routes from './routes';
import { PersistGate } from 'redux-persist/integration/react';
import './index.css';
import 'react-loading-skeleton/dist/skeleton.css';
import * as Sentry from '@sentry/react';
import environment from './environment';

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

{
  environment.nodeEnv !== 'development'
    ? Sentry.init({
        dsn:
          environment.main_url === 'fmtm.hotosm.org'
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
      })
    : null;
}

ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <RouterProvider router={routes} />
    </PersistGate>
  </Provider>,
  document.getElementById('app'),
);
if (process.env.NODE_ENV === 'production') {
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
if (process.env.NODE_ENV === 'development') {
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (let registration of registrations) {
      registration.unregister();
    }
  });
}
