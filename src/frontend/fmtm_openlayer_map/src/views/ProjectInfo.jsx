import React from "react";
import CoreModules from "fmtm/CoreModules";
import ProjectInfoSidebar from "../components/ProjectInfo/ProjectInfoSidebar";
import ProjectInfomap from "../components/ProjectInfo/ProjectInfomap";

const ProjectInfo = () => {
  return (
    <>
      <CoreModules.Box
        sx={{
          px: 3,
          py: 1,
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <CoreModules.Box>
          <CoreModules.Typography variant="h1" color="#929db3">
            #14455
          </CoreModules.Typography>
          <CoreModules.Typography variant="subtitle1">
            Union of Brazilian Mappers of OSM (UMBRAOSM)
          </CoreModules.Typography>
        </CoreModules.Box>
        <CoreModules.Button
          variant="outlined"
          color="error"
          size="small"
          sx={{ width: "fit-content", height: "fit-content" }}
        >
          Monitoring
        </CoreModules.Button>
      </CoreModules.Box>
      <CoreModules.Box sx={{ display: "flex", flex: 1, pb: 2 }}>
        {/* Project Info side bar */}
        <ProjectInfoSidebar
          projectId="#14455"
          projectName="Union of Brazilian Mappers of OSM (UMBRAOSM)"
        />
        <CoreModules.Box
          sx={{
            boxSizing: "content-box",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            gap: 1,
            px: 2,
          }}
        >
          <ProjectInfomap />
          <CoreModules.Box
            sx={{
              display: "flex",
              flexDirection: "row",
              justifyContent: "center",
              gap: 2,
            }}
          >
            <CoreModules.Button
              variant="outlined"
              color="error"
              sx={{ width: "fit-content" }}
            >
              Convert
            </CoreModules.Button>
            <CoreModules.Button
              variant="outlined"
              color="error"
              sx={{ width: "fit-content" }}
            >
              Download
            </CoreModules.Button>
          </CoreModules.Box>
          <CoreModules.Card sx={{ flex: 1 }}>
            <CoreModules.CardContent>
              Lorem ipsum dolor, sit amet consectetur adipisicing elit. Laborum
              atque soluta qui repudiandae molestias quam veritatis iure magnam
              omnis sequi possimus laboriosam, sed error incidunt numquam eius
              unde ducimus voluptatem.
            </CoreModules.CardContent>
          </CoreModules.Card>
        </CoreModules.Box>
      </CoreModules.Box>
    </>
  );
};

export default ProjectInfo;
