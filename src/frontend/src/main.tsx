import '@/index.css';
import 'ol/ol.css';
import 'react-loading-skeleton/dist/skeleton.css';

import axios from 'axios';
import React from 'react';
import ReactDOM from 'react-dom';
// Uncomment for React 18
// import { createRoot } from 'react-dom/client';

import environment from '@/environment';
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

(function sentryInit() {
  // Immediately invoked function to enable Sentry monitoring
  if (import.meta.env.MODE === 'development' || import.meta.env.BASE_URL !== 'fmtm.hotosm.org') {
    return;
  }
  console.log('Adding Sentry');

  import('@sentry/react').then((Sentry) => {
    Sentry.init({
      dsn: 'https://35c80d0894e441f593c5ac5dfa1094a0@o68147.ingest.sentry.io/4505557311356928',
      integrations: [
        new Sentry.BrowserTracing({
          // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
          tracePropagationTargets: ['https://fmtm.hotosm.org/'],
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
})();

(function matomoTrackingInit() {
  // Immediately invoked function to enable Matomo tracking
  if (import.meta.env.MODE === 'development' || import.meta.env.BASE_URL !== 'fmtm.hotosm.org') {
    return;
  }
  console.log('Adding Matomo');

  var _paq = (window._paq = window._paq || []);
  /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
  _paq.push(['requireConsent']);
  _paq.push(['setDomains', ['fmtm.hotosm.org']]);
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']); // Tracks downloads
  _paq.push(['trackVisibleContentImpressions']); // Tracks content blocks
  (function () {
    var u = '//matomo.hotosm.org/';
    _paq.push(['setTrackerUrl', u + 'matomo.php']);
    _paq.push(['setSiteId', environment.matomoTrackingId]);
    var d = document,
      g = d.createElement('script'),
      s = d.getElementsByTagName('script')[0];
    g.async = true;
    g.src = u + 'matomo.js';
    s.parentNode.insertBefore(g, s);
  })();
})();

// React 17 setup
ReactDOM.render(<App />, document.getElementById('app'));

// // React 18 setup
// createRoot(document.getElementById('app')!).render(
//   <App />,
// );
