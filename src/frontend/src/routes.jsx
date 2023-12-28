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
import UnderConstruction from './views/UnderConstruction';
import ErrorBoundary from './views/ErrorBoundary';
import NewProjectDetails from './views/NewProjectDetails';
import ProjectDetailsV2 from './views/ProjectDetailsV2';

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
        element: (
          <ErrorBoundary>
            <Home />
          </ErrorBoundary>
        ),
      },
      {
        path: '/organization',
        element: (
          <ErrorBoundary>
            <Organization />
          </ErrorBoundary>
        ),
      },
      {
        path: '/createOrganization',
        element: (
          <ErrorBoundary>
            <CreateOrganization />
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
        path: '/projectInfo/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div></div>}>
              <ErrorBoundary>
                <ProjectInfo />
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

      // {
      //   path: '/project_details/:id',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <ProjectDetails />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      {
        path: '/project_details/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <NewProjectDetails />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: '/newproject_details/:id',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <ProjectDetailsV2 />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      // {
      //   path: '/create-project',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <CreateProject />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      // {
      //   path: '/upload-area',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <CreateProject />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      // {
      //   path: '/data-extract',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <CreateProject />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      // {
      //   path: '/define-tasks',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <CreateProject />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      // {
      //   path: '/select-form',
      //   element: (
      //     <ProtectedRoute>
      //       <Suspense fallback={<div>Loading...</div>}>
      //         <ErrorBoundary>
      //           <CreateProject />
      //         </ErrorBoundary>
      //       </Suspense>
      //     </ProtectedRoute>
      //   ),
      // },
      {
        path: '/basemap-selection',
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
        path: '/select-form',
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
        path: '/edit-project/project-details/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/upload-area/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/data-extract/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/split-tasks/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/select-form/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
              </ErrorBoundary>
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: 'edit-project/basemap-selection/:projectId',
        element: (
          <ProtectedRoute>
            <Suspense fallback={<div>Loading...</div>}>
              <ErrorBoundary>
                <EditProject />
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
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

export default routes;
