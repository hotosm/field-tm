import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { LoginActions } from '@/store/slices/LoginSlice';
import { refreshCookies, getUserDetailsFromApi } from '@/utilfunctions/login';
import { useAppDispatch } from '@/types/reduxTypes';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// import '@hotosm/ui/components/Tracking';
import '@hotosm/ui/dist/style.css';
import '@hotosm/ui/dist/components';

import environment from '@/environment';
import AppRoutes from '@/routes';
import { store, persistor } from '@/store/Store';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

const RefreshUserCookies = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const refreshUserDetails = async () => {
      try {
        if (!window.location.pathname.includes('osmauth')) {
          // Do not do this on the /osmauth page after OSM callback / redirect
          const refreshSuccess = await refreshCookies();
          if (refreshSuccess) {
            // Call /auth/me to populate the user details in the header
            const apiUser = await getUserDetailsFromApi();
            if (apiUser) {
              dispatch(LoginActions.setAuthDetails(apiUser));
            } else {
              console.error('Failed to fetch user details after cookie refresh.');
            }
          } else {
            // Reset frontend login state on 401
            dispatch(LoginActions.setAuthDetails(null));
          }
        }
      } catch (err) {
        console.error('Unexpected error in RefreshUserCookies:', err);
      }
    };

    refreshUserDetails();
  }, [dispatch]);

  return null; // Renders nothing
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <RouterProvider router={AppRoutes} />
          <RefreshUserCookies />
          <hot-tracking site-id={environment.matomoTrackingId} domain={'fmtm.hotosm.org'}></hot-tracking>
        </PersistGate>
      </Provider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
};

export default App;
