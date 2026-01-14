import '@/index.css';
import '@/styles/tailwind.css';
import 'ol/ol.css';
import 'react-loading-skeleton/dist/skeleton.css';

import * as Sentry from '@sentry/react';
import axios from 'axios';
import { createRoot } from 'react-dom/client';

import App from './App';

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
  if (typeof msg !== 'string') {
    consoleError(...args);
  } else if (!SUPPRESSED_WARNINGS.some((entry) => msg.includes(entry))) {
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

// Initialize Sentry for production monitoring
const sentryEnabled =
  import.meta.env.MODE !== 'development' && window.location.hostname === 'fmtm.hotosm.org';

if (sentryEnabled) {
  console.log('Adding Sentry');
  Sentry.init({
    dsn: 'https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928',
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: ['https://fmtm.hotosm.org/'],
    // Performance Monitoring
    tracesSampleRate: 1.0, // Capture 100% of the transactions, reduce in production!
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  });
}

// React 19 setup with Sentry error handlers
createRoot(document.getElementById('app')!, {
  // React 19 exposes hooks for Sentry error tracking
  // Callback called when an error is thrown and not caught by an Error Boundary.
  onUncaughtError: sentryEnabled
    ? Sentry.reactErrorHandler((error, errorInfo) => {
        console.warn('Uncaught error', error, errorInfo.componentStack);
      })
    : undefined,
  // Callback called when React catches an error in an Error Boundary.
  onCaughtError: sentryEnabled ? Sentry.reactErrorHandler() : undefined,
  // Callback called when React automatically recovers from errors.
  onRecoverableError: sentryEnabled ? Sentry.reactErrorHandler() : undefined,
}).render(<App />);
