import React from 'react';
import {
    createBrowserRouter,
} from "react-router-dom";
import Home from './views/Home';
import Login from './views/Login';
import Create from './views/Create';
import Tabbed from './views/Tabbed';
import Forgot from './views/Forgot';
import MainView from './views/MainView';
import ProjectDetails from "map/ProjectDetails";


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
                    element: <ProjectDetails />,
                },
            ],
        },
    ]
);

export default routes;
