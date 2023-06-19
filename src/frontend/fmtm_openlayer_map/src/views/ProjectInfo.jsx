import React, { useEffect } from "react";
import CoreModules from "fmtm/CoreModules";
import ProjectInfoSidebar from "../components/ProjectInfo/ProjectInfoSidebar";
import ProjectInfomap from "../components/ProjectInfo/ProjectInfomap";
import environment from "fmtm/environment";
import {
  fectchConvertToOsmDetails,
  fetchInfoTask,
  postDownloadProjectBoundary,
} from "../api/task";

const ProjectInfo = () => {
  const dispatch = CoreModules.useDispatch();

  const taskInfo = CoreModules.useSelector((state) => state.task.taskInfo);
  const params = CoreModules.useParams();
  const encodedId = params.projectId;
  const decodedId = environment.decode(encodedId);

  const handleDownload = () => {
    console.log("lkjhgfghjk");
    dispatch(
      postDownloadProjectBoundary(
        `${environment.baseApiUrl}/projects/2/download`
      )
    );
  };

  const handleConvert = () => {
    dispatch(
      fectchConvertToOsmDetails(
        `${environment.baseApiUrl}/submission/convert-to-osm?project_id=1&task_id=2`
      )
    );
  };

  useEffect(() => {
    dispatch(
      fetchInfoTask(
        `${environment.baseApiUrl}/tasks/tasks-features/?project_id=${decodedId}`
      )
    );
  }, []);
  const projectInfo = CoreModules.useSelector(
    (state) => state.project.projectInfo
  );

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
            #{projectInfo?.id}
          </CoreModules.Typography>
          <CoreModules.Typography variant="subtitle1">
            {projectInfo?.title}
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
      <CoreModules.Box sx={{ display: "flex", pb: 2, height: "80vh" }}>
        {/* Project Info side bar */}
        <ProjectInfoSidebar
          projectId={projectInfo?.id}
          projectName={projectInfo?.title}
          taskInfo={taskInfo}
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
              onClick={handleConvert}
            >
              Convert
            </CoreModules.Button>
            <CoreModules.Button
              variant="outlined"
              color="error"
              sx={{ width: "fit-content" }}
              onClick={handleDownload}
            >
              Download
            </CoreModules.Button>
          </CoreModules.Box>
          <CoreModules.Card>
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
