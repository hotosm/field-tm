import React from 'react';
import AssetModules from '@/shared/AssetModules';
import CoreModules from '@/shared/CoreModules';
import ProjectInfoCountSkeleton from '@/components/ProjectInfo/ProjectInfoCountCardSkeleton';

const ProjectInfoCountCard = () => {
  const taskData = CoreModules.useAppSelector((state) => state.task.taskData);
  const isTaskLoading = CoreModules.useAppSelector((state) => state.task.taskLoading);

  const totalTaskInfoCount = [
    {
      count: taskData.task_count,
      title: 'Total Tasks',
      icon: <AssetModules.TaskIcon sx={{ color: '#d73f3e', fontSize: { xs: '35px', xl: '50px' } }} />,
    },
    {
      count: taskData.submission_count,
      title: 'Total Submissions',
      icon: <AssetModules.SubmissionIcon sx={{ color: '#d73f3e', fontSize: { xs: '35px', xl: '50px' } }} />,
    },
    {
      count: taskData.feature_count,
      title: 'Total Features',
      icon: <AssetModules.FeatureIcon sx={{ color: '#d73f3e', fontSize: { xs: '35px', xl: '50px' } }} />,
    },
  ];
  return (
    <div className="scrollbar fmtm-overflow-x-scroll sm:fmtm-overflow-x-hidden">
      {isTaskLoading ? (
        <ProjectInfoCountSkeleton />
      ) : (
        <div className="fmtm-flex fmtm-gap-5 fmtm-w-full fmtm-p-[2px]">
          {totalTaskInfoCount.map((taskInfo, i) => (
            <div key={i}>
              <CoreModules.Card>
                <div className="fmtm-w-fit xl:fmtm-gap-0 fmtm-p-4 xl:fmtm-min-w-[15.62rem]">
                  <h1
                    style={{
                      color: '#d73f3e',
                      margin: '0px',
                    }}
                  >
                    {taskInfo.count}
                  </h1>
                  <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-leading-4 fmtm-gap-4">
                    <p className="fmtm-text-lg xl:fmtm-text-xl">{taskInfo.title}</p>
                    {taskInfo.icon}
                  </div>
                </div>
              </CoreModules.Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectInfoCountCard;
