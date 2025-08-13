import React, { useState, useEffect } from 'react';
import environment from '@/environment';
import MapStyles from '@/hooks/MapStyles';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { project_status, task_event as taskEventEnum, task_state as taskStateEnum, task_event } from '@/types/enums';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { GetProjectTaskActivity } from '@/api/Project';
import { Modal } from '@/components/common/Modal';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { taskSubmissionInfoType } from '@/models/task/taskModel';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';
import { useAddNewTaskEventMutation } from '@/api/task/index';
import { ProjectActions } from '@/store/slices/ProjectSlice';

type dialogPropType = {
  taskId: number;
  feature: Record<string, any>;
};

type taskListStateType = {
  value: string;
  key: string;
  btnType: 'primary-red' | 'primary-grey' | 'link-red' | 'secondary-red';
};

export default function Dialog({ taskId, feature }: dialogPropType) {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();
  const geojsonStyles = MapStyles();

  const [list_of_task_actions, set_list_of_task_actions] = useState<taskListStateType[]>([]);
  const [task_state, set_task_state] = useState(taskStateEnum.UNLOCKED_TO_MAP);
  const [currentTaskInfo, setCurrentTaskInfo] = useState<taskSubmissionInfoType>();
  const [toggleMappedConfirmationModal, setToggleMappedConfirmationModal] = useState(false);

  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const projectTaskActivityList = useAppSelector((state) => state?.project?.projectTaskActivity);

  const isOrganizationAdmin = useIsOrganizationAdmin(projectInfo?.organisation_id as number);
  const isProjectManager = useIsProjectManager(projectInfo?.id as number);

  const currentProjectId: string = params.id;
  const projectIndex = projectData.findIndex((project) => project.id == parseInt(currentProjectId));
  const selectedTask = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.id == taskId;
    })?.[0],
  };

  const checkIfTaskAssignedOrNot = (taskEvent) => {
    return (
      selectedTask?.actioned_by_username === authDetails?.username ||
      selectedTask?.actioned_by_username === null ||
      task_event.MAP === taskEvent
    );
  };

  useEffect(() => {
    if (taskId) {
      dispatch(
        GetProjectTaskActivity(
          `${import.meta.env.VITE_API_URL}/tasks/${selectedTask?.id}/history?project_id=${currentProjectId}&comments=false`,
        ),
      );
    }
  }, [taskId]);

  useEffect(() => {
    if (taskInfo?.length === 0) return;
    const currentTaskInfo = taskInfo?.filter((task) => selectedTask?.index === +task?.task_id);
    if (currentTaskInfo?.[0]) {
      setCurrentTaskInfo(currentTaskInfo?.[0]);
    }
  }, [taskId, taskInfo, selectedTask]);

  useEffect(() => {
    if (projectIndex != -1) {
      const findCorrectTaskStateIndex = environment.tasksStatus.findIndex(
        (data) => data.label == selectedTask.task_state,
      );
      set_task_state(selectedTask.task_state as taskStateEnum);

      // Get all available actions given current state
      const taskActionsList =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStateIndex]?.['action'] : [];
      set_list_of_task_actions(taskActionsList);
    }
  }, [projectTaskActivityList, taskId, selectedTask]);

  const { mutate: addNewTaskEventMutate, isPending: isAddNewTaskEventPending } = useAddNewTaskEventMutation({
    id: selectedTask?.id,
    params: { project_id: +currentProjectId },
    options: {
      onSuccess: ({ data }) => {
        dispatch(
          CommonActions.SetSnackBar({
            message: `Task #${selectedTask.index} has been updated to ${data.state}`,
            variant: 'success',
          }),
        );

        feature.setStyle(geojsonStyles[data.state]);
        const prevProperties = feature.getProperties();
        const isTaskLocked = [taskStateEnum.LOCKED_FOR_MAPPING, taskStateEnum.LOCKED_FOR_VALIDATION].includes(
          data.state,
        );
        const updatedProperties = { ...prevProperties, actioned_by_uid: isTaskLocked ? data.user_sub : null };
        feature.setProperties(updatedProperties);
        dispatch(
          ProjectActions.UpdateProjectTaskBoundries({
            projectId: currentProjectId,
            taskId: data.task_id,
            actioned_by_uid: data.user_sub,
            actioned_by_username: data.username,
            task_state: data.state,
          }),
        );
      },
      onError: () => {
        dispatch(
          CommonActions.SetSnackBar({
            message: `Failed to update Task #${taskId}`,
          }),
        );
      },
    },
  });

  const handleOnClick = async (event: React.MouseEvent<HTMLElement>) => {
    const btnId = event.currentTarget.dataset.btnid;
    if (!btnId) return;
    const selectedAction = taskEventEnum[btnId];

    addNewTaskEventMutate({
      event: selectedAction,
      user_sub: authDetails?.sub,
    });
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
                variant="primary-red"
                onClick={() => {
                  setToggleMappedConfirmationModal(false);
                }}
              >
                CONTINUE MAPPING
              </Button>
              <Button
                btnId="FINISH"
                variant="primary-grey"
                onClick={(e) => {
                  handleOnClick(e);
                  setToggleMappedConfirmationModal(false);
                }}
                disabled={isAddNewTaskEventPending}
              >
                MARK AS FULLY MAPPED
              </Button>
            </div>
          </div>
        }
        className=""
      />
      {projectInfo.status === project_status.PUBLISHED && (
        <>
          {list_of_task_actions?.length > 0 && (
            <div
              className={`empty:fmtm-hidden fmtm-grid fmtm-border-t-[1px] fmtm-p-2 sm:fmtm-p-5 ${
                list_of_task_actions?.length === 1 ? 'fmtm-grid-cols-1' : 'fmtm-grid-cols-2 fmtm-gap-2'
              }`}
            >
              {list_of_task_actions?.map((data, index) => {
                return checkIfTaskAssignedOrNot(data.value) || isOrganizationAdmin || isProjectManager ? (
                  <Button
                    key={index}
                    variant={data.btnType}
                    btnId={data.value}
                    btnTestId="StartMapping"
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
                    className="!fmtm-w-full"
                    disabled={isAddNewTaskEventPending}
                  >
                    {data.key.toUpperCase()}
                  </Button>
                ) : null;
              })}
            </div>
          )}
        </>
      )}
      {task_state !== taskStateEnum.UNLOCKED_TO_MAP && task_state !== taskStateEnum.LOCKED_FOR_MAPPING && (
        <div className="fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <Button
            variant="primary-red"
            onClick={() => navigate(`/project-submissions/${params.id}?tab=table&task_id=${taskId}`)}
            className="!fmtm-w-full"
          >
            GO TO TASK SUBMISSION
          </Button>
        </div>
      )}
    </div>
  );
}
