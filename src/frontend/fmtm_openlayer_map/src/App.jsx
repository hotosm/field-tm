
import React, { useEffect, useState } from "react";
import './index.css'
import ReactDOM from "react-dom";
import "../node_modules/ol/ol.css";
import { persistor, store } from "./store/store";
import MainView from "./views/MainView";
import { Provider, useDispatch, useSelector } from "react-redux";
import { PersistGate } from 'redux-persist/integration/react';
import environment from "fmtm/environment";
import { ProjectById } from "./api/Project";


export default function App() {

  const stateHome = useSelector(state => state.home)
  const dispatch = useDispatch();

  useEffect(() => {
    if (stateHome.projectId != null) {
      dispatch(ProjectById(`${environment.baseApiUrl}/projects/${environment.decode(stateHome.projectId)}`))
    }
  }, [stateHome.projectId])
  
  return (
    <MainView />
  )
}
ReactDOM.render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <App />
    </PersistGate>
  </Provider>
  ,
  document.getElementById("app")
);
