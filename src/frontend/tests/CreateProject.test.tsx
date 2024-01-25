import React from 'react';
import MainView from '@/views/MainView';
import { Provider } from 'react-redux';
import { store } from '@/store/Store';
import { renderWithRouter } from '@/utilfunctions/testUtils';
import { expect, it, describe } from 'vitest';

describe('Frontend Application Running', () => {
  it('renders App.jsx without errors', () => {
    // Render the App component in a virtual DOM environment
    const { container } = renderWithRouter(
      <Provider store={store}>
        <MainView />
      </Provider>,
    );

    // Assert that the component renders without any errors
    expect(container).toBeDefined();
  });
});
