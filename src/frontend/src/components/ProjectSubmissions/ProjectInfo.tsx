import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { useNavigate } from 'react-router-dom';

const ProjectInfo = () => {
  const navigate = useNavigate();
  const params = CoreModules.useParams();
  const encodedId = params.projectId;
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const projectDashboardDetail = CoreModules.useAppSelector((state) => state.project.projectDashboardDetail);
  const projectDashboardLoading = CoreModules.useAppSelector((state) => state.project.projectDashboardLoading);

  const dataCard = [
    {
      title: 'Tasks',
      count: projectDashboardDetail?.total_tasks,
      icon: <AssetModules.TaskIcon sx={{ color: 'white', fontSize: { xs: '35px', xl: '40px' } }} />,
    },
    {
      title: 'Contributors',
      count: projectDashboardDetail?.total_contributors,
      icon: <AssetModules.PeopleAltIcon sx={{ color: 'white', fontSize: { xs: '35px', xl: '40px' } }} />,
    },
    {
      title: 'Submissions',
      count: projectDashboardDetail?.total_submission,
      icon: <AssetModules.SubmissionIcon sx={{ color: 'white', fontSize: { xs: '35px', xl: '40px' } }} />,
    },
  ];

  const ProjectDataCard = ({ data }) => (
    <div className="fmtm-bg-white fmtm-rounded-lg fmtm-min-w-[12.5rem] fmtm-p-2 fmtm-px-4 md:fmtm-p-4 md:fmtm-shadow-[0px_10px_20px_0px_rgba(96,96,96,0.1)] fmtm-flex fmtm-items-center fmtm-gap-4">
      <div className="fmtm-bg-primaryRed fmtm-rounded-full fmtm-p-2">{data.icon}</div>
      <div className="fmtm-flex fmtm-flex-col fmtm-items-start">
        <h2 className="fmtm-text-lg sm:fmtm-text-xl md:fmtm-text-xl fmtm-text-[#706E6E] fmtm-font-bold">
          {data.title}
        </h2>
        <h2 className="fmtm-text-xl sm:fmtm-text-2xl md:fmtm-text-2xl fmtm-font-bold fmtm-text-primaryRed">
          {data.count}
        </h2>
      </div>
    </div>
  );

  const widthStyle = window.innerWidth >= 640 ? { width: 'calc(100% - 80px)' } : { width: '100%' };

  return (
    <div style={widthStyle} className="sm:fmtm-ml-2 fmtm-border-b-[1px] fmtm-border-gray-300 fmtm-pb-10">
      <div className="fmtm-pb-4">
        <p className="fmtm-text-[#706E6E] fmtm-text-base">
          <span
            className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-200"
            onClick={() => navigate(`/newproject_details/${encodedId}`)}
          >
            {projectInfo?.title}{' '}
          </span>
          <span> &gt; </span>
          <span className="fmtm-text-black">Dashboard</span>
        </p>
      </div>
      <div className=" fmtm-flex fmtm-flex-col xl:fmtm-flex-row fmtm-w-full sm:fmtm-items-center fmtm-gap-10 fmtm-mt-3">
        {projectDashboardLoading ? (
          <CoreModules.Skeleton className="!fmtm-w-full sm:!fmtm-w-[30rem] 2xl:!fmtm-w-[34rem] !fmtm-h-[8rem] !fmtm-rounded-xl" />
        ) : (
          <div className="fmtm-w-full fmtm-min-w-0 sm:fmtm-max-w-[37rem] fmtm-bg-white fmtm-rounded-lg fmtm-p-5 fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-shadow-[0px_10px_20px_0px_rgba(96,96,96,0.1)]">
            <h2 className="fmtm-text-2xl fmtm-text-[#545454] fmtm-font-bold">{projectInfo?.title}</h2>
            <div>
              <p className="fmtm-text-base fmtm-text-[#706E6E]">
                Created On:{' '}
                <span>
                  {projectDashboardDetail?.created
                    ? `${projectDashboardDetail?.created?.split('T')[0]} ${projectDashboardDetail?.created
                        ?.split('T')[1]
                        ?.split('.')[0]}`
                    : '-'}
                </span>
              </p>
              <p className="fmtm-text-base fmtm-text-[#706E6E]">
                Last active:{' '}
                <span>{projectDashboardDetail?.last_active ? projectDashboardDetail?.last_active : '-'}</span>
              </p>
            </div>
          </div>
        )}
        <div className="fmtm-w-full fmtm-overflow-x-scroll scrollbar fmtm-pb-1 md:fmtm-pb-0 md:fmtm-overflow-x-visible">
          {projectDashboardLoading ? (
            <div className="fmtm-w-full fmtm-flex sm:fmtm-justify-center fmtm-gap-5">
              {Array.from({ length: 3 }).map((i) => (
                <CoreModules.Skeleton key={i} className="!fmtm-w-[12.5rem] fmtm-h-[6.25rem] !fmtm-rounded-xl" />
              ))}
            </div>
          ) : (
            <div className="fmtm-w-full fmtm-flex md:fmtm-justify-center fmtm-gap-5">
              {dataCard.map((data, i) => (
                <ProjectDataCard key={i} data={data} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectInfo;
