import React from "react";
import CoreModules from "fmtm/CoreModules";

const ProjectInfoSidebar = () => {
  const innerBoxStyles = {
    boxStyle: {
      borderBottom: "1px solid #F0F0F0",
      p: 2,
      display: "flex",
      flexDirection: "column",
      gap: 2,
      cursor: "pointer",
      borderRadius: "4px",
      "&:hover": {
        backgroundColor: "#F0FBFF",
      },
    },
  };

  return (
    <CoreModules.Box
      sx={{
        display: "flex",
        flexDirection: "column",
        background: "#F0F0F0",
        width: "60%",
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
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: "rgba(0,0,0,.1)",
              outline: "1px solid #F0F0F0",
              borderRadius: "25px",
            },
          }}
        >
          <CoreModules.CardContent sx={innerBoxStyles.boxStyle}>
            <CoreModules.Box
              sx={{ display: "flex", justifyContent: "space-between" }}
            >
              <CoreModules.Box>
                <CoreModules.Typography variant="h2" color="#929db3">
                  #14455
                </CoreModules.Typography>
                <CoreModules.Typography>3 contributors</CoreModules.Typography>
              </CoreModules.Box>
              <CoreModules.Button
                variant="outlined"
                color="error"
                sx={{ width: "fit-content", height: "fit-content" }}
                size="small"
              >
                Zoom to Task
              </CoreModules.Button>
            </CoreModules.Box>
            <CoreModules.LoadingBar
              title="Task Progress"
              totalSteps={5}
              activeStep={2}
            />
          </CoreModules.CardContent>
          <CoreModules.CardContent sx={innerBoxStyles.boxStyle}>
            <CoreModules.Box
              sx={{ display: "flex", justifyContent: "space-between" }}
            >
              <CoreModules.Box>
                <CoreModules.Typography variant="h2" color="#929db3">
                  #14455
                </CoreModules.Typography>
                <CoreModules.Typography>3 contributors</CoreModules.Typography>
              </CoreModules.Box>
              <CoreModules.Button
                variant="outlined"
                color="error"
                sx={{ width: "fit-content", height: "fit-content" }}
                size="small"
              >
                Zoom to Task
              </CoreModules.Button>
            </CoreModules.Box>
            <CoreModules.LoadingBar
              title="Task Progress"
              totalSteps={5}
              steps={5}
              activeStep={4}
            />
          </CoreModules.CardContent>
          <CoreModules.CardContent sx={innerBoxStyles.boxStyle}>
            <CoreModules.Box
              sx={{ display: "flex", justifyContent: "space-between" }}
            >
              <CoreModules.Box>
                <CoreModules.Typography variant="h2" color="#929db3">
                  #14455
                </CoreModules.Typography>
                <CoreModules.Typography>3 contributors</CoreModules.Typography>
              </CoreModules.Box>
              <CoreModules.Button
                variant="outlined"
                color="error"
                sx={{ width: "fit-content", height: "fit-content" }}
                size="small"
              >
                Zoom to Task
              </CoreModules.Button>
            </CoreModules.Box>
            <CoreModules.LoadingBar
              title="Task Progress"
              totalSteps={5}
              steps={5}
              activeStep={3}
            />
          </CoreModules.CardContent>
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
