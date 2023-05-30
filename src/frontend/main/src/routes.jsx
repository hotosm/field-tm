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
import CreateOrganization from './views/CreateOrganization';
import Authorized from './views/Authorized';
import SubmissionDetails from './views/SubmissionDetails';

const ProjectDetails = React.lazy(() => import('map/ProjectDetails'));
const Submissions = React.lazy(() => import('map/Submissions'));
const Tasks = React.lazy(() => import('map/Tasks'));

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
      {
        path: '/createOrganization',
        element: <CreateOrganization />,
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
      {
        path: '/project/:projectId/tasks/:taskId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <Tasks />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      // {
      //     path: "/recoveraccess",
      //     element: <Forgot />,
      // },
      {
        path: '/project/:projectId/tasks/:taskId/submission/:instanceId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <SubmissionDetails />
            </Suspense>
          </ProtectedRoute>
        ),
      },
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
        path: '/osmauth',
        element:<Suspense fallback={<div>Loading...</div>}>
                  <Authorized/>
                </Suspense>
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

export default routes;
