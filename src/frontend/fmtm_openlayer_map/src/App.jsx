
import './index.css'
import ReactDOM from "react-dom";
import { store } from "fmtm/Store";
import routes from "./routes";
import CoreModules from 'fmtm/CoreModules'

ReactDOM.render(
  <CoreModules.Provider store={store}>
    <CoreModules.RouterProvider router={routes} />
  </CoreModules.Provider>
  ,
  document.getElementById("app")
);
