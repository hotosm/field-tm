import React, { useState, useEffect } from 'react';
import environment from '@/environment';
import ProjectTaskStatus from '@/api/ProjectTaskStatus';
import MapStyles from '@/hooks/MapStyles';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_priority_str } from '@/types/enums';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';

export default function Dialog({ taskId, feature, map, view }) {
  const navigate = useNavigate();
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const loading = CoreModules.useAppSelector((state) => state.common.loading);
  const [list_of_task_status, set_list_of_task_status] = useState([]);
  const [task_status, set_task_status] = useState('READY');

  const geojsonStyles = MapStyles();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const currentProjectId = environment.decode(params.id);
  const currentTaskId = environment.encode(taskId);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task.id == taskId;
    })?.[0],
  };

  useEffect(() => {
    if (projectIndex != -1) {
      const currentStatus = {
        ...projectData[projectIndex].taskBoundries.filter((task) => {
          return task.id == taskId;
        })[0],
      };
      const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex(
        (data) => data.label == currentStatus.task_status,
      );
      const tasksStatus =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['label'] : '';
      set_task_status(tasksStatus);
      const tasksStatusList =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['action'] : [];

      set_list_of_task_status(tasksStatusList);
    }
  }, [projectData, taskId, feature]);

  const handleOnClick = (event) => {
    const status = task_priority_str[event.currentTarget.dataset.btnid];
    const body = token != null ? { ...token } : {};
    const geoStyle = geojsonStyles[event.currentTarget.dataset.btnid];
    if (event.currentTarget.dataset.btnid != undefined) {
      if (body.hasOwnProperty('id')) {
        dispatch(
          ProjectTaskStatus(
            `${import.meta.env.VITE_API_URL}/tasks/${taskId}/new_status/${status}`,
            geoStyle,
            projectData,
            currentProjectId,
            feature,
            map,
            view,
            taskId,
            body,
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
    currentStatus?.locked_by_username === token?.username || currentStatus?.locked_by_username === null;

  return (
    <div className="fmtm-flex fmtm-flex-col">
      {list_of_task_status?.length > 0 && (
        <div
          className={`fmtm-grid fmtm-border-t-[1px] fmtm-p-5 ${
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
        <div className="fmtm-p-5 fmtm-border-t">
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
        <div className="fmtm-p-5 fmtm-border-t">
          <Button
            btnText="GO TO ODK"
            btnType="primary"
            type="submit"
            className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={() => {
              document.location.href = 'intent://getodk.org/#Intent;scheme=app;package=org.odk.collect.android;end';
            }}
          />
        </div>
      )}
    </div>
  );
}
