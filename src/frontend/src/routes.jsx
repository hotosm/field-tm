import React, { Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import Landing from '@/views/Landing';
import Home from '@/views/Home';
import MainView from '@/views/MainView';
import ProtectedRoute from '@/utilities/ProtectedRoute';
import NotFoundPage from '@/views/NotFound404';
import OsmAuth from '@/views/OsmAuth';
import PlaywrightTempLogin from '@/views/PlaywrightTempLogin';
import CreateProject from '@/views/CreateProject';
import ErrorBoundary from '@/views/ErrorBoundary';
import ProjectDetails from '@/views/ProjectDetails';
import ManageUsers from '@/views/ManageUsers';
import Invite from '@/views/Invite';

const routes = createBrowserRouter([
  {
    element: <MainView />,
    children: [
      {
        path: '/',
        element: (
          <ErrorBoundary>
            <Landing />
          </ErrorBoundary>
        ),
      },
      {
        path: '/explore',
        element: (
          <ErrorBoundary>
            <Home />
          </ErrorBoundary>
        ),
      },
      {
        path: '/project/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <ProjectDetails />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/create-project/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/create-project',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/osmauth',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <ErrorBoundary>
              <OsmAuth />
            </ErrorBoundary>
          </Suspense>
        ),
      },
      {
        path: '/playwright-temp-login',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <ErrorBoundary>
              <PlaywrightTempLogin />
            </ErrorBoundary>
          </Suspense>
        ),
      },
      {
        path: '/manage/user',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <ManageUsers />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
      {
        path: '/invite',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <Invite />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
    ],
  },
]);

export default routes;
