import React, { Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import Home from '@/views/Home';
import MainView from '@/views/MainView';
import ProtectedRoute from '@/utilities/ProtectedRoute';
import NotFoundPage from '@/views/NotFound404';
import Organisation from '@/views/Organisation';
import CreateOrganization from '@/views/CreateOrganization';
import ApproveOrganization from '@/views/ApproveOrganization';
import OsmAuth from '@/views/OsmAuth';
import PlaywrightTempLogin from '@/views/PlaywrightTempLogin';
import SubmissionDetails from '@/views/SubmissionDetails';
import CreateProject from '@/views/CreateProject';
import UnderConstruction from '@/views/UnderConstruction';
import ErrorBoundary from '@/views/ErrorBoundary';
import ProjectDetails from '@/views/ProjectDetails';
import ProjectSubmissions from '@/views/ProjectSubmissions';
import ManageProject from '@/views/ManageProject';
import ManageUsers from '@/views/ManageUsers';
import DataConflation from '@/views/DataConflation';
import OrganizationDashboard from '@/views/OrganizationDashboard';
import ManageOrganization from '@/views/ManageOrganization';
import Invite from '@/views/Invite';

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
        path: '/organization',
        element: (
          <ProtectedRoute>
            <ErrorBoundary>
              <Organisation />
            </ErrorBoundary>
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/new',
        element: (
          <ProtectedRoute>
            <ErrorBoundary>
              <CreateOrganization />
            </ErrorBoundary>
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/approve/:id',
        element: (
          <ProtectedRoute>
            <ErrorBoundary>
              <ApproveOrganization />
            </ErrorBoundary>
          </ProtectedRoute>
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
        path: '/project-submissions/:projectId/tasks/:taskId/submission/:instanceId',
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
        path: '/under-construction/',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <UnderConstruction />
          </Suspense>
        ),
      },
      {
        path: '/manage/organization/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <ManageOrganization />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/manage/project/:id',
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
        path: '/conflate-data/:projectId/:taskId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <DataConflation />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <OrganizationDashboard />
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
