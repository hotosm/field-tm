import React from 'react';
import CoreModules from '../../shared/CoreModules';
import ProjectCard from './ProjectCard';
import environment from '../../environment';
import ProjectInfoSidebarSkeleton from './ProjectInfoSidebarSkeleton';

const ProjectInfoSidebar = ({ projectId, taskInfo }) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const taskInfoData = Array.from(taskInfo);
  const selectedTask = CoreModules.useAppSelector((state) => state.task.selectedTask);
  const isTaskLoading = CoreModules.useAppSelector((state) => state.task.taskLoading);

  const encodedId = params.projectId;
  const onTaskClick = (taskId) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(taskId));
  };
  const innerBoxStyles = {
    boxStyle: {
      borderBottom: '1px solid #F0F0F0',
      p: 2,
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      cursor: 'pointer',
      borderRadius: '4px',
      '&:hover': {
        backgroundColor: '#F0FBFF',
      },
    },
  };

  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        background: 'white',
        width: '100%',
        gap: 2,
      }}
      className="fmtm-mb-5"
    >
      <div className="fmtm-w-full md:fmtm-h-[80vh] fmtm-p-1 fmtm-overflow-x-hidden fmtm-overflow-y-scroll scrollbar fmtm-bg-white fmtm-border-[1px] fmtm-border-gray-200 fmtm-shadow-sm fmtm-rounded-md">
        {isTaskLoading ? (
          <div>
            {Array.from({ length: 5 }).map((i) => (
              <div id={i} key={i}>
                <ProjectInfoSidebarSkeleton />
              </div>
            ))}
          </div>
        ) : (
          <div>
            {taskInfoData?.map((task, index) => (
              <CoreModules.CardContent
                key={index}
                sx={{
                  ...innerBoxStyles.boxStyle,
                  backgroundColor: task.task_id === selectedTask ? '#F0FBFF' : '#FFFFFF',
                }}
                onClick={() => onTaskClick(+task.task_id)}
              >
                <CoreModules.Box className="fmtm-flex fmtm-justify-between">
                  <CoreModules.Box sx={{ flex: 1 }}>
                    <CoreModules.Typography variant="h1" color="#929db3">
                      #{task.task_id}
                    </CoreModules.Typography>
                  </CoreModules.Box>
                  <div className="fmtm-flex fmtm-gap-2 fmtm-items-end fmtm-flex-col sm:fmtm-flex-row md:fmtm-flex-col lg:fmtm-flex-row">
                    <CoreModules.Link
                      to={`/project/${encodedId}/tasks/${environment.encode(task.task_id)}`}
                      style={{
                        display: 'flex',
                        justifyContent: 'flex-end',
                        textDecoration: 'none',
                      }}
                    >
                      <CoreModules.Button
                        variant="outlined"
                        color="error"
                        sx={{ width: 'fit-content', height: 'fit-content' }}
                        size="small"
                        className="fmtm-truncate"
                      >
                        Go To Task Submissions
                      </CoreModules.Button>
                    </CoreModules.Link>
                    <CoreModules.Button
                      variant="outlined"
                      color="error"
                      sx={{ width: 'fit-content', height: 'fit-content' }}
                      size="small"
                      className="fmtm-truncate"
                    >
                      Zoom to Task
                    </CoreModules.Button>
                  </div>
                </CoreModules.Box>
                <CoreModules.LoadingBar
                  title="Task Progress"
                  totalSteps={task.feature_count}
                  activeStep={task.submission_count}
                />
              </CoreModules.CardContent>
            ))}
          </div>
        )}
      </div>
      {/* <CoreModules.Card
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
      </CoreModules.Card> */}
    </CoreModules.Box>
  );
};

export default ProjectInfoSidebar;
