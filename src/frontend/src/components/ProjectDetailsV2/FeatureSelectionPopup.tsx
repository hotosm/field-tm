// Popup used to display task feature info & link to ODK Collect

import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import environment from '@/environment';
import { useParams } from 'react-router-dom';
import { UpdateEntityStatus } from '@/api/Project';
import { TaskFeatureSelectionProperties } from '@/store/types/ITask';
import { UpdateTaskStatus } from '@/api/ProjectTaskStatus';
import MapStyles from '@/hooks/MapStyles';

type TaskFeatureSelectionPopupPropType = {
  taskId: number;
  featureProperties: TaskFeatureSelectionProperties | null;
  taskFeature: Record<string, any>;
};

const TaskFeatureSelectionPopup = ({ featureProperties, taskId, taskFeature }: TaskFeatureSelectionPopupPropType) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = useParams();
  const geojsonStyles = MapStyles();
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const entityOsmMap = CoreModules.useAppSelector((state) => state.project.entityOsmMap);

  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const currentProjectId = params.id || '';
  const [task_status, set_task_status] = useState('READY');
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const projectTaskActivityList = CoreModules.useAppSelector((state) => state?.project?.projectTaskActivity);
  const taskBoundaryData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const updateEntityStatusLoading = CoreModules.useAppSelector((state) => state.project.updateEntityStatusLoading);
  const currentTaskInfo = {
    ...taskBoundaryData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.index == taskId;
    })?.[0],
  };
  const geoStyle = geojsonStyles['LOCKED_FOR_MAPPING'];
  const entity = entityOsmMap.find((x) => x.osm_id === featureProperties?.osm_id);

  useEffect(() => {
    if (projectIndex != -1) {
      const currentStatus = projectTaskActivityList.length > 0 ? projectTaskActivityList[0].status : 'READY';
      const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex((data) => data?.label == currentStatus);
      const tasksStatus =
        taskFeature?.id_ != undefined ? environment?.tasksStatus[findCorrectTaskStatusIndex]?.['label'] : '';
      set_task_status(tasksStatus);
    }
  }, [projectTaskActivityList, taskId, taskFeature, entityOsmMap]);

  return (
    <div
      className={`fmtm-duration-1000 fmtm-z-[10002] fmtm-h-fit ${
        taskModalStatus
          ? 'fmtm-bottom-[4.4rem] md:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-[25rem]'
          : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(40vh)] md:fmtm-left-[calc(100vw)] fmtm-w-[100vw]'
      } fmtm-fixed
        fmtm-rounded-t-3xl fmtm-border-opacity-50`}
    >
      <div
        className={`fmtm-absolute fmtm-top-[17px] fmtm-right-[20px] ${
          taskModalStatus ? '' : 'fmtm-hidden'
        }  fmtm-cursor-pointer fmtm-flex fmtm-items-center fmtm-gap-3`}
      >
        <div title="Close">
          <AssetModules.CloseIcon
            style={{ width: '20px' }}
            className="hover:fmtm-text-primaryRed"
            onClick={() => dispatch(ProjectActions.ToggleTaskModalStatus(false))}
          />
        </div>
      </div>
      <div
        className={`fmtm-bg-[#fbfbfb] ${
          taskModalStatus ? 'sm:fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)] fmtm-border-b sm:fmtm-border-b-0' : ''
        } fmtm-rounded-t-2xl md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl`}
      >
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-p-3 sm:fmtm-p-5">
          <h4 className="fmtm-text-lg fmtm-font-bold">Feature: {featureProperties?.osm_id}</h4>
        </div>

        <div className="fmtm-h-fit fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
            <p>
              <span className="fmtm-font-semibold">Tags: </span>
              <span className="fmtm-text-primaryRed fmtm-overflow-hidden fmtm-line-clamp-2">
                {featureProperties?.tags}
              </span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Timestamp: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.timestamp}</span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Changeset: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.changeset}</span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Version: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.version}</span>
            </p>
          </div>
        </div>
        {(task_status === 'READY' || task_status === 'LOCKED_FOR_MAPPING') && (
          <div className="fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
            <Button
              btnText="MAP FEATURE IN ODK"
              btnType="primary"
              type="submit"
              className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
              disabled={entity?.status !== 0}
              isLoading={updateEntityStatusLoading}
              onClick={() => {
                const xformId = projectInfo.xform_id;
                const entity = entityOsmMap.find((x) => x.osm_id === featureProperties?.osm_id);
                const entityUuid = entity ? entity.id : null;

                if (!xformId || !entityUuid) {
                  return;
                }

                dispatch(
                  UpdateEntityStatus(`${import.meta.env.VITE_API_URL}/projects/${currentProjectId}/entity/status`, {
                    entity_id: entityUuid,
                    status: 1,
                    label: `Task ${taskId} Feature ${entity.osm_id}`,
                  }),
                );

                if (task_status === 'READY') {
                  dispatch(
                    UpdateTaskStatus(
                      `${import.meta.env.VITE_API_URL}/tasks/${currentTaskInfo?.id}/new-status/1`,
                      currentProjectId,
                      taskId.toString(),
                      authDetails,
                      { project_id: currentProjectId },
                      geoStyle,
                      taskBoundaryData,
                      taskFeature,
                    ),
                  );
                }

                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
                  navigator.userAgent,
                );

                if (isMobile) {
                  // Load entity in ODK Collect by intent
                  document.location.href = `odkcollect://form/${xformId}?existing=${entityUuid}`;
                } else {
                  dispatch(
                    CommonActions.SetSnackBar({
                      open: true,
                      message: 'Requires a mobile phone with ODK Collect.',
                      variant: 'warning',
                      duration: 3000,
                    }),
                  );
                }
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskFeatureSelectionPopup;
