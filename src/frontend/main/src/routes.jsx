import React from 'react';
import {
    createBrowserRouter,
    Navigate
} from "react-router-dom";
import Home from './views/Home';
import Login from './views/Login';
import Create from './views/Create';
import Tabbed from './views/Tabbed';
import Forgot from './views/Forgot';
import MainView from './views/MainView';
import { Suspense } from 'react';
import CreateProject from './views/CreateProject';
import NewPage from './views/NewPage';

const ProjectDetails = React.lazy(() => import('map/ProjectDetails'));
const routes = createBrowserRouter(
    [
        {
            element: <MainView />,
            children: [
                {
                    path: "/",
                    element: <Home />,
                },
                {
                    path: '/explore', 
                    element: <Navigate to="/" />,
                },
                {
                    path: "/tabbed",
                    element: <Tabbed />,
                },
                {
                    path: "/login",
                    element: <Login />,
                },
                {
                    path: "/signup",
                    element: <Create />,
                },
                {
                    path: "/recoveraccess",
                    element: <Forgot />,
                },
                {
                    path: '/project_details/:id',
                    element: <Suspense fallback={<div></div>}>
                        <ProjectDetails />
                    </Suspense>
                },
                {
                    path: '/newpage/:id',
                    element: <Suspense fallback={<div></div>}>
                        <NewPage />
                    </Suspense>
                },
                {
                    path: '/create-project',
                    element: <Suspense fallback={<div>Loading...</div>}>
                        <CreateProject />
                    </Suspense>
                },
                {
                    path: '/upload-area',
                    element: <Suspense fallback={<div>Loading...</div>}>
                        <CreateProject />
                    </Suspense>
                },
            ],
        },
    ]
);

export default routes;
