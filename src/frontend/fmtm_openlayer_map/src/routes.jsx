import MainView from "./views/MainView";
import Home from "./views/Home";
import CoreModules from "fmtm/CoreModules";
import React, { Suspense } from "react";

const routes = CoreModules.createBrowserRouter([
  {
    element: <MainView />,
    children: [
      {
        path: "/:id",
        element: (
          <Suspense fallback={<div>Loading...</div>}>
            <Home />
          </Suspense>
        ),
      },
    ],
  },
]);

export default routes;
