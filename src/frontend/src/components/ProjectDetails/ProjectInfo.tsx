import React, { useEffect, useRef, useState } from 'react';
import AssetModules from '@/shared/AssetModules.js';
import ProjectIcon from '@/assets/images/project_icon.png';
import CoreModules from '@/shared/CoreModules';
import { useAppSelector } from '@/types/reduxTypes';
import { entity_state } from '@/types/enums';
import { EntityOsmMap } from '@/models/project/projectModel';

const ProjectInfo: React.FC = () => {
  const paraRef = useRef<HTMLParagraphElement>(null);
  const [seeMore, setSeeMore] = useState(false);
  const [descLines, setDescLines] = useState(1);
  const projectInfo = useAppSelector((state) => state?.project?.projectInfo);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const projectEntities = useAppSelector((state) => state?.project?.entityOsmMap);
  const projectEntitiesLoading = useAppSelector((state) => state?.project?.entityOsmMapLoading);

  useEffect(() => {
    if (paraRef.current) {
      const lineHeight = parseFloat(getComputedStyle(paraRef.current).lineHeight);
      const lines = Math.floor(paraRef.current.clientHeight / lineHeight);
      setDescLines(lines);
    }
  }, [projectInfo, paraRef.current]);

  const projectLastActiveDate: Date | null = projectEntities.reduce((latestDate: Date | null, entity: EntityOsmMap) => {
    const updatedAt = Date.parse(entity.updated_at);
    return updatedAt && (!latestDate || updatedAt > latestDate.getTime()) ? new Date(updatedAt) : latestDate;
  }, null);

  const projectTotalFeatures: number = projectEntities.length;

  const projectMappedFeatures: number = projectEntities.filter(
    (entity: EntityOsmMap) => entity.status === entity_state.SURVEY_SUBMITTED,
  ).length;

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-mt-3  fmtm-overflow-y-scroll scrollbar fmtm-pr-1">
      <div>
        <p className="fmtm-font-bold">Description</p>
        {projectDetailsLoading ? (
          <div>
            {Array.from({ length: 7 }).map((_, index) => (
              <CoreModules.Skeleton key={index} />
            ))}
            <CoreModules.Skeleton key="last" className="!fmtm-w-[80px]" />
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
          <p className="fmtm-font-bold">Mapped Features</p>
          {projectEntitiesLoading ? (
            <CoreModules.Skeleton className="!fmtm-w-[60px] fmtm-ml-[15%]" />
          ) : (
            <p className="fmtm-text-center fmtm-text-[#706E6E]">
              {projectMappedFeatures} / {projectTotalFeatures}
            </p>
          )}
        </div>
        <div>
          <p className="fmtm-font-bold">Last Contribution</p>
          {projectEntitiesLoading ? (
            <CoreModules.Skeleton className="!fmtm-w-[70px] fmtm-ml-[20%]" />
          ) : (
            <p className="fmtm-text-center fmtm-text-[#706E6E] fmtm-capitalize">
              {projectLastActiveDate ? projectLastActiveDate.toLocaleString() : '-'}
            </p>
          )}
        </div>
      </div>
      <div>
        <p className="fmtm-font-bold fmtm-mb-1">Organized By:</p>
        {projectDetailsLoading ? (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-5">
            <CoreModules.Skeleton className="!fmtm-w-[2.81rem] fmtm-h-[2.81rem] !fmtm-rounded-full fmtm-overflow-hidden" />
            <CoreModules.Skeleton className="!fmtm-w-[180px]" />
          </div>
        ) : (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
            <div className="fmtm-w-10 fmtm-h-10 fmtm-overflow-hidden fmtm-rounded-full fmtm-bg-white fmtm-flex fmtm-justify-center fmtm-items-center">
              <img
                src={projectInfo?.organisation_logo ? projectInfo?.organisation_logo : ProjectIcon}
                alt="Organization Photo"
              />
            </div>
            <p>{projectInfo?.organisation_name}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectInfo;
