import React from "react";
import environment from "fmtm/environment";
import ProjectTaskStatus from "../api/ProjectTaskStatus";
import MapStyles from "../hooks/MapStyles";
import CoreModules from "fmtm/CoreModules";

export default function Dialog({ taskId, feature, map, view }) {
  // const featureStatus = feature.id_ != undefined ? feature.id_.replace("_", ",").split(',')[1] : null;
  const projectData = CoreModules.useSelector(
    (state) => state.project.projectTaskBoundries
  );
  const geojsonStyles = MapStyles();
  const dispatch = CoreModules.useDispatch();
  const params = CoreModules.useParams();
  const currentProjectId = environment.decode(params.id);
  const projectIndex = projectData.findIndex(
    (project) => project.id == currentProjectId
  );
  const currentStatus = {
    ...projectData[projectIndex].taskBoundries.filter((task) => {
      return task.id == taskId;
    })[0],
  };

  const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex(
    (data) => data.label == currentStatus.task_status_str
  );
  const tasksStatus =
    feature.id_ != undefined
      ? environment.tasksStatus[findCorrectTaskStatusIndex]["label"]
      : "";
  const tasksStatusList =
    feature.id_ != undefined
      ? environment.tasksStatus[findCorrectTaskStatusIndex]["action"]
      : [];
  const tasksList = environment.tasksStatus.map((status) => {
    return status.key;
  });

  const handleOnClick = (event) => {
    const status = event.target.id;
    const body = {
      username: "mohamed",
      id: 1,
    };
    const geoStyle = geojsonStyles[status];
    if (event.target.id != undefined) {
      dispatch(
        ProjectTaskStatus(
          `${environment.baseApiUrl}/tasks/${taskId}/new_status/${status}`,
          geoStyle,
          projectData,
          currentProjectId,
          feature,
          map,
          view,
          taskId,
          body
        )
      );
    }
  };

  return (
    <CoreModules.Stack direction={"column"} spacing={2}>
      <CoreModules.Stack direction={"row"} pl={1}>
        <CoreModules.Typography fontWeight={'bold'} variant="h3">
          {`Task : ${taskId}`}
        </CoreModules.Typography>
      </CoreModules.Stack>
      <CoreModules.Stack direction={"row"} pl={1}>
        <CoreModules.Typography variant="h3">
          {`STATUS : ${tasksStatus.replaceAll("_", " ")}`}
        </CoreModules.Typography>
      </CoreModules.Stack>

      {tasksStatusList.map((data, index) => {
        return tasksStatusList.length != 0 ? (
          <CoreModules.Button
            id={data.value}
            key={index}
            variant="contained"
            color="error"
            onClick={handleOnClick}
            disabled={false}
          >
            {data.key}
          </CoreModules.Button>
        ) : (
          <CoreModules.Button
            id={data.value}
            key={index}
            variant="contained"
            color="error"
            onClick={handleOnClick}
            disabled={true}
          >
            {data.key}
          </CoreModules.Button>
        );
      })}
    </CoreModules.Stack>
  );
}
