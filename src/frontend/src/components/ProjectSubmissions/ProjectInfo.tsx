import React from 'react';
import CoreModules from '@/shared/CoreModules';

const ProjectInfo = () => {
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const projectDashboardDetail = CoreModules.useAppSelector((state) => state.project.projectDashboardDetail);
  const projectDashboardLoading = CoreModules.useAppSelector((state) => state.project.projectDashboardLoading);

  const dataCard = [
    { title: 'Tasks', count: projectDashboardDetail?.total_tasks },
    { title: 'Contributors', count: projectDashboardDetail?.total_contributors },
    { title: 'Submissions', count: projectDashboardDetail?.total_submission },
  ];

  const ProjectDataCard = ({ data }) => (
    <div className="fmtm-border-[1px] fmtm-border-primaryRed fmtm-bg-white fmtm-rounded-2xl fmtm-min-w-[7.5rem] fmtm-w-[7.5rem] sm:fmtm-w-[8.5rem] 2xl:fmtm-w-[10rem] fmtm-flex fmtm-flex-col fmtm-items-center fmtm-p-2 md:fmtm-p-4 fmtm-gap-2 fmtm-shadow-md fmtm-shadow-red-300">
      {projectDashboardLoading ? (
        <CoreModules.Skeleton className="!fmtm-w-[100px] fmtm-h-[30px]" />
      ) : (
        <h2 className="fmtm-font-archivo fmtm-text-xl sm:fmtm-text-2xl md:fmtm-text-[1.7rem] 2xl:fmtm-text-[2rem] fmtm-font-bold fmtm-text-primaryRed">
          {data.count}
        </h2>
      )}
      {projectDashboardLoading ? (
        <CoreModules.Skeleton className="!fmtm-w-[100px] fmtm-h-[20px]" />
      ) : (
        <h4 className="fmtm-font-archivo fmtm-text-lg sm:fmtm-text-xl md::fmtm-text-[1.2rem] 2xl:fmtm-text-[1.5rem] fmtm-text-[#7A7676]">
          {data.title}
        </h4>
      )}
    </div>
  );
  return (
    <div className="fmtm-w-full sm:fmtm-ml-2 fmtm-border-b-[1px] fmtm-border-gray-300 fmtm-pb-10">
      <div className="fmtm-pb-4">
        <p className="fmtm-text-[#706E6E] fmtm-font-archivo fmtm-text-sm">
          <span>Projects </span>
          <span> &gt; </span>
          <span>Dashboard</span>
        </p>
      </div>
      <div className=" fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-w-full sm:fmtm-items-center fmtm-gap-10 fmtm-mt-3">
        <div className="fmtm-w-full fmtm-min-w-0 sm:fmtm-max-w-[37rem] fmtm-bg-primary-100 fmtm-rounded-2xl fmtm-p-5 fmtm-flex fmtm-flex-col fmtm-gap-5">
          {false ? (
            <div>
              <CoreModules.Skeleton className="!fmtm-w-full" />
              <CoreModules.Skeleton className="!fmtm-w-[200px]" />
            </div>
          ) : (
            <h2 className="fmtm-text-xl fmtm-font-archivo">{projectInfo?.title}</h2>
          )}
          <div>
            <p className="fmtm-text-sm fmtm-text-[#706E6E] fmtm-font-archivo">
              Created On:{' '}
              {projectDashboardLoading ? (
                <CoreModules.Skeleton className="!fmtm-w-[100px]" />
              ) : (
                <span>
                  {projectDashboardDetail?.created
                    ? `${projectDashboardDetail?.created?.split('T')[0]} ${projectDashboardDetail?.created
                        ?.split('T')[1]
                        ?.split('.')[0]}`
                    : '-'}
                </span>
              )}
            </p>
            <p className="fmtm-text-sm fmtm-text-[#706E6E] fmtm-font-archivo">
              Last active:{' '}
              {projectDashboardLoading ? (
                <CoreModules.Skeleton className="!fmtm-w-[100px]" />
              ) : (
                <span>{projectDashboardDetail?.last_active ? projectDashboardDetail?.last_active : '-'}</span>
              )}
            </p>
          </div>
        </div>
        <div className="fmtm-w-full fmtm-overflow-x-scroll scrollbar fmtm-pb-1 sm:fmtm-pb-0 sm:fmtm-overflow-x-visible">
          <div className="fmtm-w-full fmtm-flex sm:fmtm-justify-center fmtm-gap-5">
            {dataCard.map((data, i) => (
              <ProjectDataCard key={i} data={data} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectInfo;
