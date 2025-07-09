import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import { EntityOsmMap } from '@/models/project/projectModel';

type propType = {
  entities: EntityOsmMap[];
};

const ProjectInfo = ({ entities }: propType) => {
  const navigate = useNavigate();
  const params = CoreModules.useParams();
  const projectId = params.projectId;
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const submissionContributorsData = useAppSelector((state) => state.submission.submissionContributors);

  const projectTaskList = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectTaskList.findIndex((project) => project.id == +projectId);
  const taskActivities = projectTaskList?.[projectIndex]?.taskBoundries;
  const projectDetailsLoading = useAppSelector((state) => state.project.projectDetailsLoading);
  const entityOsmMapLoading = useAppSelector((state) => state.project.entityOsmMapLoading);
  const projectCreationDate = projectInfo?.created_at ? projectInfo?.created_at?.split('T')[0] : '-';
  const submissionContributorsLoading = useAppSelector((state) => state.submission.submissionContributorsLoading);

  const latestDateSorted = entities
    ?.map((entry) => new Date(entry?.updated_at)) // Convert to Date objects
    .sort((a, b) => b - a)?.[0]
    ?.toISOString();

  const updatedDateTime = latestDateSorted ? latestDateSorted?.split('T')[0] : '-';
  const submissionCount = entities?.reduce((total, entity) => {
    const entitySubmissionCount = entity?.submission_ids?.split(',')?.length || 0;
    return total + entitySubmissionCount;
  }, 0);

  const dataCard = [
    {
      title: 'Tasks',
      count: taskActivities?.length,
      icon: <AssetModules.TaskIcon sx={{ color: 'white', fontSize: { xs: '35px', xl: '40px' } }} />,
    },
    {
      title: 'Contributors',
      count: submissionContributorsData?.length,
      icon: <AssetModules.PeopleAltIcon sx={{ color: 'white', fontSize: { xs: '35px', xl: '40px' } }} />,
    },
    {
      title: 'Submissions',
      count: submissionCount,
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

  return (
    <div className="fmtm-w-full sm:fmtm-ml-2 fmtm-border-b-[1px] fmtm-border-gray-300 fmtm-pb-10">
      {projectDetailsLoading ? (
        <CoreModules.Skeleton style={{ width: '150px' }} className="fmtm-mb-1" />
      ) : (
        <div className="fmtm-pb-4">
          <p className="fmtm-text-[#706E6E] fmtm-text-base">
            <span
              className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-200"
              onClick={() => navigate(`/project/${projectId}`)}
            >
              {projectInfo.name}{' '}
            </span>
            <span> &gt; </span>
            <span className="fmtm-text-black">Dashboard</span>
          </p>
        </div>
      )}
      <div className=" fmtm-flex fmtm-flex-col xl:fmtm-flex-row fmtm-w-full sm:fmtm-items-center fmtm-gap-10 fmtm-mt-3">
        {projectDetailsLoading || entityOsmMapLoading ? (
          <CoreModules.Skeleton className="!fmtm-w-full sm:!fmtm-w-[30rem] 2xl:!fmtm-w-[34rem] !fmtm-h-[8rem] !fmtm-rounded-xl" />
        ) : (
          <div className="fmtm-w-full fmtm-min-w-0 sm:fmtm-max-w-[37rem] fmtm-bg-white fmtm-rounded-lg fmtm-p-5 fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-shadow-[0px_10px_20px_0px_rgba(96,96,96,0.1)]">
            <h2 className="fmtm-text-2xl fmtm-text-[#545454] fmtm-font-bold">{projectInfo.name}</h2>
            <div>
              <p className="fmtm-text-base fmtm-text-[#706E6E]">
                Created On:
                <span>{projectCreationDate}</span>
              </p>
              <p className="fmtm-text-base fmtm-text-[#706E6E]">Last active: {updatedDateTime}</p>
            </div>
          </div>
        )}
        <div className="fmtm-w-full fmtm-overflow-x-scroll scrollbar fmtm-pb-1 md:fmtm-pb-0 md:fmtm-overflow-x-visible">
          {projectDetailsLoading || submissionContributorsLoading || entityOsmMapLoading ? (
            <div className="fmtm-w-full fmtm-flex sm:fmtm-justify-center fmtm-gap-5">
              {Array.from({ length: 3 }).map((_, i) => (
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
