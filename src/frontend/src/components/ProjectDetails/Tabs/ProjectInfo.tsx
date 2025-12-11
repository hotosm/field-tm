import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Tooltip } from '@mui/material';
import ProjectIcon from '@/assets/images/project_icon.png';
import { useAppSelector } from '@/types/reduxTypes';
import { field_mapping_app, project_status } from '@/types/enums';
import { EntityOsmMap } from '@/models/project/projectModel';
import CoreModules from '@/shared/CoreModules';
import ProjectInfoSkeleton from '@/components/Skeletons/ProjectDetails/ProjectInfoSkeleton';
import StatusChip from '@/components/common/StatusChip';
import QRContainer from '../QRContainer';

const projectStatusVariantMap: Record<project_status, 'default' | 'info' | 'success' | 'error'> = {
  [project_status.DRAFT]: 'default',
  [project_status.PUBLISHED]: 'info',
  [project_status.COMPLETED]: 'success',
  [project_status.ARCHIVED]: 'error',
};

const ProjectInfo: React.FC = () => {
  const params = useParams();
  const paraRef = useRef<HTMLParagraphElement>(null);

  const projectId = params.id;
  const [seeMore, setSeeMore] = useState(false);
  const [descLines, setDescLines] = useState(1);

  const projectInfo = useAppSelector((state) => state?.project?.projectInfo);
  const projectTaskBoundries = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const projectEntities = useAppSelector((state) => state?.project?.entityOsmMap);
  const projectEntitiesLoading = useAppSelector((state) => state?.project?.entityOsmMapLoading);
  // @ts-ignore
  const authDetails = useAppSelector((state) => state?.login?.authDetails);

  const projectTasks = projectTaskBoundries.find((project) => project.id.toString() === projectId)?.taskBoundries;

  const taskProgress = projectTasks?.reduce(
    (total, task) => {
      const taskState = task.task_state;
      if (taskState === 'UNLOCKED_TO_VALIDATE' || taskState === 'LOCKED_FOR_VALIDATION') {
        total.mapped += 1;
      }
      if (taskState === 'UNLOCKED_DONE') {
        total.validated += 1;
      }
      return total;
    },
    { mapped: 0, validated: 0 },
  );

  const projectLastActiveDate: Date | null = projectEntities.reduce((latestDate: Date | null, entity: EntityOsmMap) => {
    const updatedAt = Date.parse(entity.updated_at);
    return updatedAt && (!latestDate || updatedAt > latestDate.getTime()) ? new Date(updatedAt) : latestDate;
  }, null);

  const projectTotalFeatures: number = projectEntities.length;
  const projectMappedFeatures: number = projectEntities.filter((entity: EntityOsmMap) => entity.status > 1).length;

  useEffect(() => {
    if (paraRef.current) {
      const lineHeight = parseFloat(getComputedStyle(paraRef.current).lineHeight);
      const lines = Math.floor(paraRef.current.clientHeight / lineHeight);
      setDescLines(lines);
    }
  }, [projectInfo, paraRef.current]);

  if (projectDetailsLoading) return <ProjectInfoSkeleton />;
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-overflow-y-scroll scrollbar fmtm-pr-1 fmtm-pb-6">
      <div>
        <p className="fmtm-button fmtm-text-red-medium">Description</p>
        <div>
          <p className={`${!seeMore ? 'fmtm-line-clamp-[7]' : ''} fmtm-body-md fmtm-text-grey-900 `} ref={paraRef}>
            {projectInfo?.description}
          </p>
          {descLines >= 7 && (
            <p
              className="fmtm-body-md fmtm-text-red-medium hover:fmtm-text-red-dark hover:fmtm-cursor-pointer fmtm-w-fit"
              onClick={() => setSeeMore(!seeMore)}
            >
              ... {!seeMore ? 'See More' : 'See Less'}
            </p>
          )}
        </div>
      </div>
      <div>
        <p className="fmtm-button fmtm-text-grey-900">Project ID</p>
        <p className="fmtm-body-md fmtm-text-grey-800">#{projectInfo.id}</p>
      </div>
      <div>
        <p className="fmtm-button fmtm-text-grey-900">Project Status</p>
        <StatusChip
          label={projectInfo.status?.toLowerCase() || ''}
          status={projectStatusVariantMap[projectInfo.status as project_status]}
        />
      </div>
      <div>
        <p className="fmtm-button fmtm-text-grey-900">Project Area</p>
        <p className="fmtm-body-md fmtm-text-grey-800">{projectInfo.location_str || '-'}</p>
      </div>
      {projectInfo?.field_mapping_app !== field_mapping_app.QField && (
        <div>
          <p className="fmtm-button fmtm-text-grey-900">Last Contribution</p>
          <p className="fmtm-body-md fmtm-text-grey-800">
            {projectLastActiveDate ? projectLastActiveDate.toLocaleString() : '-'}
          </p>
        </div>
      )}
      <div>
        <p className="fmtm-button fmtm-text-grey-900">Organized By</p>
        <img
          src={projectInfo?.organisation_logo ? projectInfo?.organisation_logo : ProjectIcon}
          alt="Organization Photo"
          className="fmtm-max-w-[2.625rem]"
        />
      </div>
      {projectInfo?.field_mapping_app !== field_mapping_app.QField && (
        <div>
          {projectEntitiesLoading ? (
            <CoreModules.Skeleton width={150} height={14} />
          ) : (
            <p className="fmtm-body-md fmtm-mb-1">
              <span className="fmtm-text-red-medium">{projectMappedFeatures}</span>{' '}
              <span className="fmtm-text-grey-800">/{projectTotalFeatures} Features Mapped</span>
            </p>
          )}
          {projectTasks && taskProgress && (
            <Tooltip
              title={
                <div>
                  <p>{projectTasks?.length} Total Tasks</p>
                  <p>{taskProgress?.mapped} Tasks Mapped</p>
                  <p>{taskProgress?.validated} Tasks Validated</p>
                </div>
              }
              placement="top"
              arrow
              componentsProps={{
                tooltip: {
                  sx: {
                    backgroundColor: '#333333',
                    color: '#ffffff',
                    fontSize: '12px',
                  },
                },
                arrow: {
                  sx: {
                    color: '#333333',
                  },
                },
              }}
            >
              <div className="fmtm-h-[0.375rem] fmtm-w-full fmtm-bg-grey-300 fmtm-rounded-xl fmtm-overflow-hidden fmtm-flex fmtm-cursor-pointer">
                <div
                  style={{
                    width: `${(taskProgress?.mapped / projectTasks?.length) * 100}%`,
                  }}
                  className={`fmtm-h-full fmtm-bg-grey-800 fmtm-rounded-r-xl`}
                />
                <div
                  style={{
                    width: `${(taskProgress?.validated / projectTasks?.length) * 100}%`,
                  }}
                  className={`fmtm-h-full fmtm-bg-grey-500 fmtm-rounded-r-xl`}
                />
              </div>
            </Tooltip>
          )}
        </div>
      )}
      <QRContainer projectInfo={projectInfo} />
    </div>
  );
};

export default ProjectInfo;
