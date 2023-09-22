import React from 'react';
import { Provider } from 'react-redux';
import { store } from '../store/Store';
import { BrowserRouter } from 'react-router-dom';
import { act, render } from '@testing-library/react';
export const renderWithRouter = (ui, { route = '/' } = {}) => {
  act(() => window.history.pushState({}, 'Test page', route));

  return {
    ...render(ui, { wrapper: BrowserRouter }),
  };
};
export const ReduxProviders = ({ children, props = { locale: 'en' }, localStore = null }) => (
  <Provider store={localStore || store}>
    <Provider {...props}>{children}</Provider>
  </Provider>
);
