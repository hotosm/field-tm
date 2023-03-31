import React from "react";
import { useState, CSSProperties } from "react";
import ClipLoader from "react-spinners/ClipLoader";
import { SyncLoader,PropagateLoader,ClockLoader,RotateLoader,MoonLoader,PulseLoader,ScaleLoader,DotLoader} from "react-spinners";
import CoreModules from "../shared/CoreModules";

const override = {
  display: "block",
  margin: "2 auto",
  borderColor: "red",
};
const Loader = ()=>{
  const appLoading = CoreModules.useSelector(state=>state.common.loading)
  const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
  return (
    <div style={{left:'50%'}} className="sweet-loading">
      <DotLoader color={`${defaultTheme.palette.error.main}`} loading={appLoading} cssOverride={override}  size={60} />
    </div>
  );
}

export default Loader;