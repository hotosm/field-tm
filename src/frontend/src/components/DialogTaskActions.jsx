import React, { useState, useEffect } from 'react';
import environment from '@/environment';
import ProjectTaskStatus from '@/api/ProjectTaskStatus';
import MapStyles from '@/hooks/MapStyles';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_priority_str } from '@/types/enums';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { GetProjectTaskActivity } from '@/api/Project';

export default function Dialog({ taskId, feature, map, view }) {
  const navigate = useNavigate();
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const taskBoundaryData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const loading = CoreModules.useAppSelector((state) => state.common.loading);
  const [list_of_task_status, set_list_of_task_status] = useState([]);
  const [task_status, set_task_status] = useState('READY');

  const geojsonStyles = MapStyles();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const currentProjectId = params.id;
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const currentStatus = {
    ...taskBoundaryData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task.id == taskId;
    })?.[0],
  };
  const projectTaskActivityList = CoreModules.useAppSelector((state) => state?.project?.projectTaskActivity);

  useEffect(() => {
    dispatch(GetProjectTaskActivity(`${import.meta.env.VITE_API_URL}/tasks/${taskId}/history/?comment=false`));
  }, [taskId]);

  useEffect(() => {
    if (projectIndex != -1) {
      const currentStatus = projectTaskActivityList.length > 0 ? projectTaskActivityList[0].status : 'READY';
      const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex((data) => data.label == currentStatus);
      const tasksStatus =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['label'] : '';
      set_task_status(tasksStatus);
      const tasksStatusList =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['action'] : [];
      set_list_of_task_status(tasksStatusList);
    }
  }, [projectTaskActivityList, taskId, feature]);

  const handleOnClick = (event) => {
    const status = task_priority_str[event.currentTarget.dataset.btnid];
    const authDetailsCopy = authDetails != null ? { ...authDetails } : {};
    const geoStyle = geojsonStyles[event.currentTarget.dataset.btnid];
    if (event.currentTarget.dataset.btnid != undefined) {
      if (authDetailsCopy.hasOwnProperty('id')) {
        dispatch(
          ProjectTaskStatus(
            `${import.meta.env.VITE_API_URL}/tasks/${taskId}/new-status/${status}`,
            geoStyle,
            taskBoundaryData,
            currentProjectId,
            feature,
            map,
            view,
            taskId,
            authDetailsCopy,
            { project_id: currentProjectId },
          ),
        );
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Something is wrong with the user.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    } else {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Oops!, Please try again.',
          variant: 'error',
          duration: 2000,
        }),
      );
    }
  };
  const checkIfTaskAssignedOrNot =
    currentStatus?.locked_by_username === authDetails?.username || currentStatus?.locked_by_username === null;

  return (
    <div className="fmtm-flex fmtm-flex-col">
      {list_of_task_status?.length > 0 && (
        <div
          className={`fmtm-grid fmtm-border-t-[1px] fmtm-p-2 sm:fmtm-p-5 ${
            list_of_task_status?.length === 1 ? 'fmtm-grid-cols-1' : 'fmtm-grid-cols-2'
          }`}
        >
          {checkIfTaskAssignedOrNot &&
            list_of_task_status?.map((data, index) => {
              return list_of_task_status?.length != 0 ? (
                <Button
                  btnId={data.value}
                  key={index}
                  onClick={handleOnClick}
                  disabled={loading}
                  btnText={data.key.toUpperCase()}
                  btnType={data.btnBG === 'red' ? 'primary' : 'other'}
                  className={`fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center ${
                    data.btnBG === 'gray'
                      ? '!fmtm-bg-[#4C4C4C] hover:!fmtm-bg-[#5f5f5f] fmtm-text-white hover:!fmtm-text-white !fmtm-border-none'
                      : data.btnBG === 'transparent'
                        ? '!fmtm-bg-transparent !fmtm-text-primaryRed !fmtm-border-none !fmtm-w-fit fmtm-mx-auto hover:!fmtm-text-red-700'
                        : ''
                  }`}
                />
              ) : null;
            })}
        </div>
      )}
      {task_status !== 'READY' && task_status !== 'LOCKED_FOR_MAPPING' && (
        <div className="fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <Button
            btnText="GO TO TASK SUBMISSION"
            btnType="primary"
            type="submit"
            className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={() => navigate(`/project-submissions/${params.id}?tab=table&task_id=${taskId}`)}
          />
        </div>
      )}
      {task_status === 'LOCKED_FOR_MAPPING' && (
        <div className="fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <Button
            btnText="GO TO ODK"
            btnType="primary"
            type="submit"
            className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={() => {
              // XForm name is constructed from lower case project title with underscores
              const projectName = projectInfo.title.toLowerCase().split(' ').join('_');
              const projectCategory = projectInfo.xform_category;
              const formName = `${projectName}_${projectCategory}`;
              document.location.href = `odkcollect://form/${formName}?task_id=${taskId}`;
              // TODO add this to each feature popup to pre-load a selected entity
              // document.location.href = `odkcollect://form/${formName}?${geomFieldName}=${entityId}`;
            }}
          />
        </div>
      )}
    </div>
  );
}
