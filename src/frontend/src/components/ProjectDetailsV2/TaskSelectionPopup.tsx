// Popup used to display task area info & QR Code for ODK Collect

import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import environment from '@/environment';
import QrcodeComponent from '@/components/QrcodeComponent';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

type TaskSelectionPopupPropType = {
  taskId: number | null;
  body: React.JSX.Element;
  feature: any;
};

const TaskSelectionPopup = ({ taskId, body, feature }: TaskSelectionPopupPropType) => {
  const params = CoreModules.useParams();
  const dispatch = useAppDispatch();

  const currentProjectId: string = params.id;
  const [task_state, set_task_state] = useState('UNLOCKED_TO_MAP');

  const taskModalStatus = useAppSelector((state) => state.project.taskModalStatus);
  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id.toString() === currentProjectId);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const selectedTask = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((indTask, i) => {
      return indTask?.id == taskId;
    })?.[0],
  };
  const checkIfTaskAssignedOrNot =
    selectedTask?.actioned_by_username === authDetails?.username || selectedTask?.actioned_by_username === null;

  useEffect(() => {
    if (projectIndex != -1) {
      const currentStatus = {
        ...projectData[projectIndex].taskBoundries.filter((task) => {
          return task?.id == taskId;
        })[0],
      };
      const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex((data) => {
        return data.label == currentStatus.task_state;
      });
      const tasksStatus =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['label'] : '';
      set_task_state(tasksStatus);
    }
  }, [projectData, taskId, feature]);

  return (
    <div
      className={`fmtm-duration-1000 fmtm-z-[10002] fmtm-h-fit ${
        taskModalStatus
          ? 'fmtm-bottom-[4.4rem] md:fmtm-bottom-0 lg:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-[25rem]'
          : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(40vh)] md:fmtm-left-[calc(100vw)] fmtm-w-[100vw]'
      } fmtm-fixed
        fmtm-rounded-t-3xl fmtm-border-opacity-50`}
    >
      <div
        className={`fmtm-absolute fmtm-top-[17px] fmtm-right-[20px] ${
          taskModalStatus ? '' : 'fmtm-hidden'
        }  fmtm-cursor-pointer fmtm-flex fmtm-items-center fmtm-gap-3`}
      >
        <div
          title="Download Tiles"
          className="fmtm-flex fmtm-items-center fmtm-gap-1 fmtm-group"
          onClick={() => {
            dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(true));
            dispatch(ProjectActions.ToggleTaskModalStatus(false));
          }}
        >
          <AssetModules.FileDownloadOutlinedIcon
            style={{ width: '20px' }}
            className="fmtm-text-primaryRed group-hover:fmtm-text-red-700"
          />
          <p className="fmtm-text-base fmtm-text-primaryRed group-hover:fmtm-text-red-700">Basemaps</p>
        </div>
        <div title="Close">
          <AssetModules.CloseIcon
            style={{ width: '20px' }}
            className="hover:fmtm-text-primaryRed"
            onClick={() => {
              dispatch(ProjectActions.ToggleTaskModalStatus(false));
              dispatch(CoreModules.TaskActions.SetSelectedTask(null));
            }}
          />
        </div>
      </div>
      <div
        className={`fmtm-bg-[#fbfbfb] ${
          taskModalStatus ? 'sm:fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)] fmtm-border-b sm:fmtm-border-b-0' : ''
        } fmtm-rounded-t-2xl md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl`}
      >
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-p-3 sm:fmtm-p-5">
          <h4 className="fmtm-text-lg fmtm-font-bold">Task: {selectedTask.index}</h4>
          <p className="fmtm-text-base fmtm-text-[#757575]">Status: {task_state}</p>
          {selectedTask?.actioned_by_username && (
            <p className="fmtm-text-base fmtm-text-[#757575]">Locked By: {selectedTask?.actioned_by_username}</p>
          )}
        </div>
        {/* only display qr code component render inside taskPopup on mobile screen */}
        <div className="sm:fmtm-hidden">
          {checkIfTaskAssignedOrNot && task_state !== 'LOCKED_FOR_MAPPING' && (
            <QrcodeComponent projectId={currentProjectId} />
          )}
        </div>
        {body}
      </div>
    </div>
  );
};

export default TaskSelectionPopup;
