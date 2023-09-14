import React from 'react';
import AssetModules from '../../shared/AssetModules';
import CoreModules from '../../shared/CoreModules';
import ProjectInfoCountSkeleton from './ProjectInfoCountCardSkeleton';

const ProjectInfoCountCard = () => {
  const taskData = CoreModules.useAppSelector((state) => state.task.taskData);
  const isTaskLoading = CoreModules.useAppSelector((state) => state.task.taskLoading);

  const totalTaskInfoCount = [
    {
      count: taskData.task_count,
      title: 'Total Tasks',
      icon: <AssetModules.TaskIcon sx={{ color: '#d73f3e', fontSize: '50px' }} />,
    },
    {
      count: taskData.submission_count,
      title: 'Total Submissions',
      icon: <AssetModules.SubmissionIcon sx={{ color: '#d73f3e', fontSize: '50px' }} />,
    },
    {
      count: taskData.feature_count,
      title: 'Total Features',
      icon: <AssetModules.FeatureIcon sx={{ color: '#d73f3e', fontSize: '50px' }} />,
    },
  ];
  return (
    <CoreModules.Box>
      <div>
        {isTaskLoading ? (
          <ProjectInfoCountSkeleton />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto auto auto',
              gap: '20px',
            }}
          >
            {totalTaskInfoCount.map((taskInfo) => (
              <div>
                <CoreModules.Card>
                  <div
                    style={{
                      gap: '0px',
                      padding: '15px',
                      minWidth: '250px',
                    }}
                  >
                    <h1
                      style={{
                        color: '#d73f3e',
                        margin: '0px',
                      }}
                    >
                      {taskInfo.count}
                    </h1>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        lineHeight: '15px',
                      }}
                    >
                      <p style={{ fontSize: '20px' }}>{taskInfo.title}</p>
                      {taskInfo.icon}
                    </div>
                  </div>
                </CoreModules.Card>
              </div>
            ))}
          </div>
        )}
      </div>
    </CoreModules.Box>
  );
};

export default ProjectInfoCountCard;
