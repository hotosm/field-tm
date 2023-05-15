import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import Home from './views/Home';
import Login from './views/Login';
import Create from './views/Create';
import Tabbed from './views/Tabbed';
import Forgot from './views/Forgot';
import MainView from './views/MainView';
import { Suspense } from 'react';
import CreateProject from './views/CreateProject';
import ProtectedRoute from './utilities/ProtectedRoute';
import NotFoundPage from './views/NotFound404';
import Organization from './views/Organization';

const ProjectDetails = React.lazy(() => import('map/ProjectDetails'));
const Submissions = React.lazy(() => import('map/Submissions'));
const routes = createBrowserRouter([
  {
    element: <MainView />,
    children: [
      {
        path: '/',
        element: <Home />,
      },
      {
        path: '/organization',
        element: <Organization />,
      },
      // {
      //     path: '/explore',
      //     element: <Navigate to="/" />,
      // },
      {
        path: '/tabbed',
        element: <Tabbed />,
      },
      {
        path: '/login',
        element: <Login />,
      },
      {
        path: '/signup',
        element: <Create />,
      },
      // {
      //     path: "/recoveraccess",
      //     element: <Forgot />,
      // },
      {
        path: '/submissions/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <Submissions />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/project_details/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ProjectDetails />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/create-project',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/upload-area',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/define-tasks',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/select-form',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/basemap-selection',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

export default routes;
