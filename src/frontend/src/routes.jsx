import React, { Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import Home from '@/views/Home';
import Tabbed from '@/views/Tabbed';
import MainView from '@/views/MainView';
import ProtectedRoute from '@/utilities/ProtectedRoute';
import NotFoundPage from '@/views/NotFound404';
import Organisation from '@/views/Organisation';
import CreateEditOrganization from '@/views/CreateEditOrganization';
import ApproveOrganization from '@/views/ApproveOrganization';
import Authorized from '@/views/Authorized';
import SubmissionDetails from '@/views/SubmissionDetails';
import CreateNewProject from '@/views/CreateNewProject';
import UnderConstruction from '@/views/UnderConstruction';
import ErrorBoundary from '@/views/ErrorBoundary';
import ProjectDetailsV2 from '@/views/ProjectDetailsV2';
import ProjectSubmissions from '@/views/ProjectSubmissions';
import ManageProject from '@/views/ManageProject';

const Submissions = React.lazy(() => import('./views/Submissions'));
const Tasks = React.lazy(() => import('./views/Tasks'));

const routes = createBrowserRouter([
  {
    element: <MainView />,
    children: [
      {
        path: '/',
        element: (
          <ErrorBoundary>
            <Home />
          </ErrorBoundary>
        ),
      },
      {
        path: '/organisation',
        element: (
          <ErrorBoundary>
            <Organisation />
          </ErrorBoundary>
        ),
      },
      {
        path: '/create-organization',
        element: (
          <ErrorBoundary>
            <CreateEditOrganization />
          </ErrorBoundary>
        ),
      },
      {
        path: '/edit-organization/:id',
        element: (
          <ErrorBoundary>
            <CreateEditOrganization />
          </ErrorBoundary>
        ),
      },
      {
        path: '/approve-organization/:id',
        element: (
          <ErrorBoundary>
            <ApproveOrganization />
          </ErrorBoundary>
        ),
      },
      // {
      //     path: '/explore',
      //     element: <Navigate to="/" />,
      // },
      {
        path: '/tabbed',
        element: (
          <ErrorBoundary>
            <Tabbed />
          </ErrorBoundary>
        ),
      },
      {
        path: '/project-submissions/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ErrorBoundary>
                <ProjectSubmissions />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },

      {
        path: '/project/:projectId/tasks/:taskId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ErrorBoundary>
                <Tasks />
              </ErrorBoundary>
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
              <ErrorBoundary>
                <SubmissionDetails />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/submissions/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ErrorBoundary>
                <Submissions />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/project_details/:id',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <ErrorBoundary>
              <ProjectDetailsV2 />
            </ErrorBoundary>
          </Suspense>
        ),
      },
      {
        path: '/create-project',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/upload-area',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/data-extract',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/split-tasks',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/select-category',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/basemap-selection',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <CreateNewProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/osmauth/',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <ErrorBoundary>
              <Authorized />
            </ErrorBoundary>
          </Suspense>
        ),
      },
      {
        path: '/under-construction/',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <UnderConstruction />
          </Suspense>
        ),
      },
      {
        path: '/manage-project/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <ManageProject />
              </ErrorBoundary>
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
