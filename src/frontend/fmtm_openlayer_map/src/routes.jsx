import React from 'react';
import {
    createBrowserRouter,
} from "react-router-dom";
import MainView from './views/MainView';
import Home from './views/Home';


const routes = createBrowserRouter(
    [
        {
            element: <MainView />,
            children: [
                {
                    path: "/:id",
                    element: <Home />,
                },
                // {
                //     path: '/project_details/:id',
                //     element: <ProjectDetails />,
                // },
            ],
        },
    ]
);

export default routes;