import React, { useState, useEffect } from 'react';
import environment from '@/environment';
import ProjectTaskStatus from '@/api/ProjectTaskStatus';
import MapStyles from '@/hooks/MapStyles';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_status as taskStatusEnum } from '@/types/enums';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { GetProjectTaskActivity } from '@/api/Project';
import { Modal } from '@/components/common/Modal';

export default function Dialog({ taskId, feature, map, view }) {
  const navigate = useNavigate();
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const taskBoundaryData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const loading = CoreModules.useAppSelector((state) => state.common.loading);
  const taskInfo = CoreModules.useAppSelector((state) => state.task.taskInfo);
  const [list_of_task_status, set_list_of_task_status] = useState([]);
  const [task_status, set_task_status] = useState('READY');
  const [currentTaskInfo, setCurrentTaskInfo] = useState();
  const [toggleMappedConfirmationModal, setToggleMappedConfirmationModal] = useState(false);

  const geojsonStyles = MapStyles();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const currentProjectId = params.id;
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const currentStatus = {
    ...taskBoundaryData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.index == taskId;
    })?.[0],
  };
  const projectTaskActivityList = CoreModules.useAppSelector((state) => state?.project?.projectTaskActivity);

  useEffect(() => {
    if (taskId) {
      dispatch(
        GetProjectTaskActivity(`${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/history/?comment=false`),
      );
    }
  }, [taskId]);

  useEffect(() => {
    if (taskInfo?.length === 0) return;
    const currentTaskInfo = taskInfo?.filter((task) => taskId == task?.index);
    if (currentTaskInfo?.[0]) {
      setCurrentTaskInfo(currentTaskInfo?.[0]);
    }
  }, [taskId, taskInfo]);

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
    const status = taskStatusEnum[event.currentTarget.dataset.btnid];
    const authDetailsCopy = authDetails != null ? { ...authDetails } : {};
    const geoStyle = geojsonStyles[event.currentTarget.dataset.btnid];
    if (event.currentTarget.dataset.btnid != undefined) {
      if (authDetailsCopy.hasOwnProperty('id')) {
        dispatch(
          ProjectTaskStatus(
            `${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/new-status/${status}`,
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
      <Modal
        onOpenChange={(openStatus) => setToggleMappedConfirmationModal(openStatus)}
        open={toggleMappedConfirmationModal}
        description={
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-10">
            <div>
              <h5 className="fmtm-text-lg">
                You have only mapped{' '}
                <span className="fmtm-text-primaryRed fmtm-font-bold">
                  {currentTaskInfo?.submission_count}/{currentTaskInfo?.feature_count}
                </span>{' '}
                features in the task area. <br /> Are you sure you wish to mark this task as complete?
              </h5>
            </div>
            <div className="fmtm-flex fmtm-gap-4 fmtm-items-center fmtm-justify-end">
              <Button
                btnText="CONTINUE MAPPING"
                btnType="primary"
                type="submit"
                className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
                onClick={() => {
                  setToggleMappedConfirmationModal(false);
                }}
              />
              <Button
                btnId="MAPPED"
                onClick={(e) => {
                  handleOnClick(e);
                  setToggleMappedConfirmationModal(false);
                }}
                disabled={loading}
                btnText="MARK AS FULLY MAPPED"
                btnType="other"
                className={`fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center !fmtm-bg-[#4C4C4C] hover:!fmtm-bg-[#5f5f5f] fmtm-text-white hover:!fmtm-text-white !fmtm-border-none`}
              />
            </div>
          </div>
        }
        className=""
      />
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
                  onClick={(e) => {
                    if (
                      data.key === 'Mark as fully mapped' &&
                      currentTaskInfo?.submission_count < currentTaskInfo?.feature_count
                    ) {
                      setToggleMappedConfirmationModal(true);
                    } else {
                      handleOnClick(e);
                    }
                  }}
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
