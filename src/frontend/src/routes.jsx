import React, { Suspense } from 'react';
import {
  createBrowserRouter,
  // Navigate,
} from 'react-router-dom';
import Home from './views/Home';
import Tabbed from './views/Tabbed';
import MainView from './views/MainView';
import CreateProject from './views/CreateProject';
import EditProject from './views/EditProject';
import ProtectedRoute from './utilities/ProtectedRoute';
import NotFoundPage from './views/NotFound404';
import Organization from './views/Organization';
import CreateOrganization from './views/CreateOrganization';
import Authorized from './views/Authorized';
import SubmissionDetails from './views/SubmissionDetails';
import CreateNewProject from './views/CreateNewProject';
import ProjectDetails from './views/ProjectDetails';

// const ProjectDetails = React.lazy(() => import('./views/ProjectDetails'));
const Submissions = React.lazy(() => import('./views/Submissions'));
const Tasks = React.lazy(() => import('./views/Tasks'));
const ProjectInfo = React.lazy(() => import('./views/ProjectInfo'));

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
        path: '/projectInfo/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ProjectInfo />{' '}
            </Suspense>
          </ProtectedRoute>
        ),
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
            <Suspense fallback={<div>Loading...</div>}>
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
        path: '/data-extract',
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
        path: '/new-create-project',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/new-upload-area',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/new-data-extract',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/new-define-tasks',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/new-select-form',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/new-basemap-selection',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <CreateNewProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/edit-project/project-details/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/upload-area/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/data-extract/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/define-tasks/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/select-form/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/basemap-selection/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <EditProject />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/osmauth/',
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <Authorized />
          </Suspense>
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
