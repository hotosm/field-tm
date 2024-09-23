import React, { useState, useEffect } from 'react';
import environment from '@/environment';
import { UpdateTaskStatus } from '@/api/ProjectTaskStatus';
import MapStyles from '@/hooks/MapStyles';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_status as taskStatusEnum } from '@/types/enums';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { GetProjectTaskActivity } from '@/api/Project';
import { Modal } from '@/components/common/Modal';
import { useAppSelector } from '@/types/reduxTypes';
import { taskSubmissionInfoType } from '@/models/task/taskModel';

type dialogPropType = {
  taskId: number;
  feature: Record<string, any>;
};

type taskListstatusType = {
  value: string;
  key: string;
  btnBG: string;
};

export default function Dialog({ taskId, feature }: dialogPropType) {
  const navigate = useNavigate();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const geojsonStyles = MapStyles();

  const [list_of_task_status, set_list_of_task_status] = useState<taskListstatusType[]>([]);
  const [task_status, set_task_status] = useState('READY');
  const [currentTaskInfo, setCurrentTaskInfo] = useState<taskSubmissionInfoType>();
  const [toggleMappedConfirmationModal, setToggleMappedConfirmationModal] = useState(false);

  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const taskBoundaryData = useAppSelector((state) => state.project.projectTaskBoundries);
  const loading = useAppSelector((state) => state.common.loading);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const projectTaskActivityList = useAppSelector((state) => state?.project?.projectTaskActivity);

  const currentProjectId: string = params.id;
  const projectIndex = projectData.findIndex((project) => project.id == parseInt(currentProjectId));
  const currentStatus = {
    ...taskBoundaryData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.index == taskId;
    })?.[0],
  };
  const checkIfTaskAssignedOrNot =
    currentStatus?.locked_by_username === authDetails?.username || currentStatus?.locked_by_username === null;

  useEffect(() => {
    if (taskId) {
      dispatch(
        GetProjectTaskActivity(`${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/history/?comment=false`),
      );
    }
  }, [taskId]);

  useEffect(() => {
    if (taskInfo?.length === 0) return;
    const currentTaskInfo = taskInfo?.filter((task) => taskId.toString() === task?.index);
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

  const handleOnClick = async (event: React.MouseEvent<HTMLElement>) => {
    const btnId = event.currentTarget.dataset.btnid;
    if (!btnId) return;
    const status = taskStatusEnum[btnId];
    const authDetailsCopy = authDetails != null ? { ...authDetails } : {};
    const geoStyle = geojsonStyles[btnId];
    if (btnId != undefined) {
      if (authDetailsCopy.hasOwnProperty('id')) {
        // if (btnId === 'MERGE_WITH_OSM') {
        //   navigate(`/conflate-data/${currentProjectId}/${taskId}`);
        //   return;
        // }
        await dispatch(
          UpdateTaskStatus(
            `${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/new-status/${status}`,
            currentProjectId,
            taskId.toString(),
            authDetailsCopy,
            { project_id: currentProjectId },
            geoStyle,
            taskBoundaryData,
            feature,
          ),
        );
        if (btnId === 'LOCKED_FOR_VALIDATION')
          navigate(`/project-submissions/${params.id}?tab=table&task_id=${taskId}`);
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
      {list_of_task_status?.length > 0 && checkIfTaskAssignedOrNot && (
        <div
          className={`fmtm-grid fmtm-border-t-[1px] fmtm-p-2 sm:fmtm-p-5 ${
            list_of_task_status?.length === 1 ? 'fmtm-grid-cols-1' : 'fmtm-grid-cols-2'
          }`}
        >
          {list_of_task_status?.map((data, index) => {
            return list_of_task_status?.length != 0 ? (
              <Button
                btnId={data.value}
                key={index}
                onClick={(e) => {
                  if (
                    data.key === 'Mark as fully mapped' &&
                    currentTaskInfo &&
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
              const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
                navigator.userAgent,
              );

              if (isMobile) {
                document.location.href = `odkcollect://form/${projectInfo.xform_id}`;
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
  );
}
