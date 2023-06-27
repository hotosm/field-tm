import React from "react";
import CoreModules from "fmtm/CoreModules";
import ProjectCard from "./ProjectCard";

const ProjectInfoSidebar = ({ taskInfo }) => {
  const dispatch = CoreModules.useDispatch();
  const taskInfoData = Array.from(taskInfo);
  const selectedTask = CoreModules.useSelector(
    (state) => state.task.selectedTask
  );

  const onTaskClick = (taskId) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(taskId));
  };
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
      <CoreModules.Card
        sx={{
          width: "100%",
          height: "50vh",
          p: 1,
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
        {taskInfoData?.map((task, index) => (
          <CoreModules.CardContent
            key={index}
            sx={{
              ...innerBoxStyles.boxStyle,
              backgroundColor:
                task.task_id === selectedTask ? "#F0FBFF" : "#FFFFFF",
            }}
            onClick={() => onTaskClick(task.task_id)}
          >
            <CoreModules.Box
              sx={{ display: "flex", justifyContent: "space-between" }}
            >
              <CoreModules.Box>
                <CoreModules.Typography variant="h1" color="#929db3">
                  #{task.task_id}
                </CoreModules.Typography>
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
              totalSteps={task.feature_count}
              activeStep={task.submission_count}
            />
          </CoreModules.CardContent>
        ))}
      </CoreModules.Card>
      <CoreModules.Card
        sx={{
          width: "100%",
          p: 2,
          height: "30vh",
          background: "white",
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
        <CoreModules.Box sx={{ borderBottom: "1px solid #F0F0F0" }}>
          <CoreModules.Typography variant="h1">
            Api Listing
          </CoreModules.Typography>
          <CoreModules.Typography>3 contributors</CoreModules.Typography>
        </CoreModules.Box>
        <CoreModules.Box
          sx={{
            display: "flex",
            // flexDirection: "row",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <ProjectCard />
          <ProjectCard />
          <ProjectCard />
        </CoreModules.Box>
      </CoreModules.Card>
    </CoreModules.Box>
  );
};

export default ProjectInfoSidebar;
