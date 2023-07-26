import React, { PropsWithChildren } from 'react'
import { render } from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'
// import { configureStore } from '@reduxjs/toolkit'
import type { PreloadedState } from '@reduxjs/toolkit'

// import type { AppStore, RootState } from '../app/store'
// As a basic setup, import your same slice reducers
import userReducer from '../features/users/userSlice'
import CoreModules from '../shared/CoreModules';

// This type interface extends the default options for render from RTL, as well
// as allows the user to specify other things such as initialState, store.
interface ExtendedRenderOptions extends Omit<any, 'queries'> {
  preloadedState?: PreloadedState<any>
  store?: any
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    // Automatically create a store instance if no store was passed in
    store = CoreModules.configureStore({ reducer: { user: userReducer }, preloadedState }),
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: PropsWithChildren<any>): any {
    return <CoreModules.Provider store={store}>{children}</CoreModules.Provider>
  }

  // Return an object with the store and all of RTL's query functions
  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) }
}