import React from "react";
import CoreModules from "fmtm/CoreModules";
import LoadingBar from "./LoadingBar";

const ProjectInfoSidebar = () => {
  return (
    <CoreModules.Box
      sx={{
        display: "flex",
        flexDirection: "column",
        background: "#F0F0F0",
        width: "60%",
        p: 2,
        gap: 2,
      }}
    >
      <CoreModules.Box
        sx={{
          display: "flex",
          flexDirection: "column",

          gap: 2,
        }}
        height="100%"
      >
        <CoreModules.Card
          sx={{
            width: "100%",
            p: 1,
            flex: 0.6,
            overflow: "hidden",
            overflowY: "auto",
            "&::-webkit-scrollbar": {
              width: "0.6em",
            },
            "&::-webkit-scrollbar-track": {
              boxShadow: "inset 0 0 6px rgba(0,0,0,0.00)",
              webkitBoxShadow: "inset 0 0 6px rgba(0,0,0,0.00)",
            },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: "rgba(0,0,0,.1)",
              outline: "1px solid #F0F0F0",
            },
          }}
        >
          <CoreModules.CardContent
            sx={{ borderBottom: "1px solid #F0F0F0", p: 2 }}
          >
            <CoreModules.Typography variant="h1">TaskId</CoreModules.Typography>
            <CoreModules.Typography>3 contributors</CoreModules.Typography>

            <CoreModules.LoadingBar />
          </CoreModules.CardContent>
          <CoreModules.Box sx={{ borderBottom: "1px solid #F0F0F0", p: 2 }}>
            <CoreModules.Typography variant="h1">TaskId</CoreModules.Typography>
            <CoreModules.Typography>3 contributors</CoreModules.Typography>
            <CoreModules.LoadingBar />
          </CoreModules.Box>
          <CoreModules.Box sx={{ borderBottom: "1px solid #F0F0F0", p: 2 }}>
            <CoreModules.Typography variant="h1">TaskId</CoreModules.Typography>
            <CoreModules.Typography>3 contributors</CoreModules.Typography>
            <CoreModules.LoadingBar />
          </CoreModules.Box>
        </CoreModules.Card>
        <CoreModules.Card
          sx={{ width: "100%", p: 1, flex: 0.4, background: "white" }}
        >
          <CoreModules.Box sx={{ borderBottom: "1px solid #F0F0F0", p: 2 }}>
            <CoreModules.Typography variant="h1">
              Api Listing
            </CoreModules.Typography>
            <CoreModules.Typography>3 contributors</CoreModules.Typography>
          </CoreModules.Box>
        </CoreModules.Card>
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default ProjectInfoSidebar;
