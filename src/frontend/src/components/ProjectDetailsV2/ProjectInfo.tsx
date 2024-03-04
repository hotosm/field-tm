import React, { useEffect, useRef, useState } from 'react';
import AssetModules from '@/shared/AssetModules.js';
import ProjectIcon from '@/assets/images/project_icon.png';
import CoreModules from '@/shared/CoreModules';
import { useAppSelector } from '@/types/reduxTypes';

const ProjectInfo = () => {
  const paraRef = useRef<any>(null);
  const [seeMore, setSeeMore] = useState(false);
  const [descLines, setDescLines] = useState(1);
  const projectInfo = useAppSelector((state) => state?.project?.projectInfo);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const projectDashboardDetail = useAppSelector((state) => state?.project?.projectDashboardDetail);
  const projectDashboardLoading = useAppSelector((state) => state?.project?.projectDashboardLoading);

  useEffect(() => {
    if (paraRef.current) {
      const lineHeight = parseFloat(getComputedStyle(paraRef.current).lineHeight);
      const lines = Math.floor(paraRef.current.clientHeight / lineHeight);
      setDescLines(lines);
    }
  }, [projectInfo, paraRef.current]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-mt-3  fmtm-h-[50vh] fmtm-overflow-y-scroll scrollbar fmtm-pr-1">
      <div>
        <p className="fmtm-font-bold">Description</p>
        {projectDetailsLoading ? (
          <div>
            {Array.from({ length: 7 }).map((i) => (
              <CoreModules.Skeleton key={i} />
            ))}
            <CoreModules.Skeleton className="!fmtm-w-[80px]" />
          </div>
        ) : (
          <div>
            <p className={`${!seeMore ? 'fmtm-line-clamp-[7]' : ''} fmtm-text-[#706E6E]`} ref={paraRef}>
              {projectInfo?.description}
            </p>
            {descLines >= 7 && (
              <p
                className="fmtm-text-primaryRed hover:fmtm-text-red-700 hover:fmtm-cursor-pointer"
                onClick={() => setSeeMore(!seeMore)}
              >
                ... {!seeMore ? 'See More' : 'See Less'}
              </p>
            )}
          </div>
        )}
      </div>
      <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
        <AssetModules.FmdGoodIcon className="fmtm-text-primaryRed" />
        {projectDetailsLoading ? (
          <CoreModules.Skeleton className="!fmtm-w-[160px]" />
        ) : (
          <p>{projectInfo?.location_str ? projectInfo?.location_str : '-'}</p>
        )}
      </div>
      <div className="fmtm-flex fmtm-justify-between fmtm-w-full">
        <div>
          <p className="fmtm-font-bold">Contributors</p>
          {projectDashboardLoading ? (
            <CoreModules.Skeleton className="!fmtm-w-[60px] fmtm-ml-[15%]" />
          ) : (
            <p className="fmtm-text-center fmtm-text-[#706E6E]">{projectDashboardDetail?.total_contributors}</p>
          )}
        </div>
        <div>
          <p className="fmtm-font-bold">Last Contribution</p>
          {projectDashboardLoading ? (
            <CoreModules.Skeleton className="!fmtm-w-[70px] fmtm-ml-[20%]" />
          ) : (
            <p className="fmtm-text-center fmtm-text-[#706E6E] fmtm-capitalize">
              {projectDashboardDetail?.last_active ? projectDashboardDetail?.last_active : '-'}
            </p>
          )}
        </div>
      </div>
      <div>
        <p className="fmtm-font-bold fmtm-mb-1">Organized By:</p>
        {projectDashboardLoading ? (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-5">
            <CoreModules.Skeleton className="!fmtm-w-[2.81rem] fmtm-h-[2.81rem] !fmtm-rounded-full fmtm-overflow-hidden" />
            <CoreModules.Skeleton className="!fmtm-w-[180px]" />
          </div>
        ) : (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
            <div className="fmtm-w-10 fmtm-h-10 fmtm-overflow-hidden fmtm-rounded-full fmtm-bg-white fmtm-flex fmtm-justify-center fmtm-items-center">
              <img
                src={
                  projectDashboardDetail?.organisation_logo ? projectDashboardDetail?.organisation_logo : ProjectIcon
                }
                alt="Organization Photo"
              />
            </div>
            <p className="fmtm-text-center fmtm-text-[#706E6E]">{projectDashboardDetail?.organisation}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectInfo;
