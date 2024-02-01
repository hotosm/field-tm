import React from 'react';
import TaskSubmissionsMap from '@/components/ProjectSubmissions/TaskSubmissionsMap';
import InputTextField from '@/components/common/InputTextField';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import { TaskCardSkeletonLoader } from '@/components/ProjectSubmissions/ProjectSubmissionsSkeletonLoader';

const TaskSubmissions = () => {
  const dispatch = CoreModules.useAppDispatch();
  const taskInfo = CoreModules.useAppSelector((state) => state.task.taskInfo);
  const taskLoading = CoreModules.useAppSelector((state) => state.task.taskLoading);

  const zoomToTask = (taskId) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(+taskId));
  };

  const TaskCard = ({ task }) => (
    <div className="fmtm-bg-red-50 fmtm-px-5 fmtm-pb-5 fmtm-pt-2 fmtm-rounded-lg">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <p>#{task?.task_id}</p>
          <div className="fmtm-flex fmtm-justify-between">
            <p>Expected Count</p>
            <p>{task?.feature_count}</p>
          </div>
          <div className="fmtm-flex fmtm-justify-between">
            <p>Submission Count</p>
            <p>{task.submission_count}</p>
          </div>
        </div>
        <div className="fmtm-flex fmtm-flex-wrap fmtm-flex-row md:fmtm-flex-col lg:fmtm-flex-row fmtm-justify-between lg:fmtm-items-center fmtm-gap-2">
          <Button btnText="View Submissions" btnType="primary" onClick={() => {}} />
          <button
            className="fmtm-border-primaryRed fmtm-border-[2px] fmtm-flex fmtm-w-fit fmtm-px-2 fmtm-py-1 fmtm-rounded-md fmtm-items-center fmtm-gap-2 fmtm-bg-white hover:fmtm-bg-gray-100 fmtm-duration-150"
            onClick={() => zoomToTask(task?.task_id)}
          >
            <AssetModules.MapIcon style={{ fontSize: '18px' }} /> <p className="fmtm-truncate">Zoom to Task</p>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="md:fmtm-h-[70vh] fmtm-flex fmtm-gap-10 fmtm-flex-col md:fmtm-flex-row">
      <div className="fmtm-w-full md:fmtm-w-[39rem] fmtm-bg-white fmtm-rounded-xl fmtm-p-5">
        <InputTextField fieldType="string" label="" onChange={() => {}} value="" placeholder="Search by task id" />
        <div className="fmtm-mt-5 fmtm-h-[58vh] fmtm-overflow-y-scroll scrollbar">
          {taskLoading ? (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
              {Array.from({ length: 10 }).map((i) => (
                <TaskCardSkeletonLoader key={i} />
              ))}
            </div>
          ) : (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
              {taskInfo?.map((task) => <TaskCard key={task.task_id} task={task} />)}
            </div>
          )}
        </div>
      </div>
      <div className="fmtm-h-[60vh] md:fmtm-h-full fmtm-w-full fmtm-rounded-xl fmtm-overflow-hidden">
        <TaskSubmissionsMap />
      </div>
    </div>
  );
};

export default TaskSubmissions;
