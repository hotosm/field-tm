import React from 'react';
import {
    createBrowserRouter,
} from "react-router-dom";
import Home from './views/Home';
import MainView from './views/MainView';
import ProjectDetails from "./views/ProjectDetails";




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
                    path: '/project_details/:id',
                    element: <ProjectDetails />,
                },
            ],
        },
    ]
);

export default routes;