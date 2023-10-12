import React from 'react';
import { screen } from '@testing-library/react';
import MainView from '../src/views/MainView';
import { store } from '../src/store/Store';
import { renderWithRouter } from '../src/utilfunctions/testUtils';
import { Provider } from 'react-redux';
import { expect, test, it, describe } from 'vitest';

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
describe('MyComponent', () => {
  test('renders the app bar with correct elements', () => {
    renderWithRouter(
      <Provider store={store}>
        <MainView />
      </Provider>,
    );

    // Check if the "EXPLORE PROJECTS" tab is rendered
    const exploreTabElement = screen.getByText('EXPLORE PROJECTS');
    expect(exploreTabElement).toBeInTheDocument();

    // Check if the "MANAGE ORGANIZATIONS" tab is rendered
    const manageOrgTabElement = screen.getByText('MANAGE ORGANIZATIONS');
    expect(manageOrgTabElement).toBeInTheDocument();
  });
});
