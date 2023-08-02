import MainView from './views/MainView';
import Home from './views/Home';
import CoreModules from 'fmtm/CoreModules';

const routes = CoreModules.createBrowserRouter(
    [
        {
            element: <MainView />,
            children: [
                {
                    path: "/:id",
                    element: <Home />,
                },
            ],
        },
    ]
);

export default routes;
