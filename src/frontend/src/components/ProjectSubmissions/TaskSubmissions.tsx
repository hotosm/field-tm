import React, { useEffect, useState } from 'react';
import TaskSubmissionsMap from '@/components/ProjectSubmissions/TaskSubmissionsMap';
import InputTextField from '@/components/common/InputTextField';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import { taskSubmissionInfoType } from '@/models/task/taskModel';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import TaskCardSkeleton from '@/components/Skeletons/ProjectSubmissions.tsx/TaskCardSkeleton';

const TaskSubmissions = () => {
  const params = useParams();
  const dispatch = useAppDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const taskLoading = useAppSelector((state) => state.task.taskLoading);
  const [searchedTaskId, setSearchedTaskId] = useState('');
  const [debouncedSearchedTaskId, setDebouncedSearchedTaskId] = useState('');
  const [taskInfoList, setTaskInfoList] = useState<taskSubmissionInfoType[]>([]);
  const [filteredTaskInfo, setFilteredTaskInfo] = useState<taskSubmissionInfoType[]>([]);
  const projectData = CoreModules.useAppSelector((state) => state?.project?.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == params?.projectId);
  const projectTaskLength = projectData[projectIndex]?.taskBoundries?.length;

  useEffect(() => {
    if (taskInfo?.length === 0 && !projectTaskLength) return;
    if (taskInfo.length === projectTaskLength) {
      setTaskInfoList(taskInfo);
    } else {
      const updatedTask: taskSubmissionInfoType[] = Array.from({ length: projectTaskLength })?.map((_, i) => {
        // TODO check this logic should be id or index for task?
        const task = taskInfo?.find((task) => parseInt(task?.index) === i + 1);
        if (task) {
          return task;
        } else {
          return {
            index: (i + 1).toString(),
            task_id: (i + 1).toString(),
            feature_count: 0,
            submission_count: 0,
            last_submission: null,
          };
        }
      });
      setTaskInfoList(updatedTask);
    }
  }, [taskInfo, projectTaskLength]);

  const zoomToTask = (taskId) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(+taskId));
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedSearchedTaskId(searchedTaskId);
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchedTaskId, 1000]);

  useEffect(() => {
    if (debouncedSearchedTaskId) {
      const searchedTaskInfoList = taskInfoList?.filter((task): boolean => {
        return task.task_id.includes(debouncedSearchedTaskId);
      });
      setFilteredTaskInfo(searchedTaskInfoList);
    } else {
      setFilteredTaskInfo(taskInfoList);
    }
  }, [debouncedSearchedTaskId, taskInfoList]);

  const TaskCard = ({ task }: { task: taskSubmissionInfoType }) => (
    <div className="fmtm-bg-red-50 fmtm-px-5 fmtm-pb-5 fmtm-pt-2 fmtm-rounded-lg">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <p>#{task?.index}</p>
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
          {!(task?.submission_count === 0 && task?.feature_count === 0) && (
            <Button variant="primary-red" onClick={() => setSearchParams({ tab: 'table', task_id: task?.task_id })}>
              View Submissions
            </Button>
          )}
          <Button variant="secondary-red" onClick={() => zoomToTask(task?.task_id)}>
            <AssetModules.MapIcon className="!fmtm-text-lg" />
            Zoom to Task
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="md:fmtm-h-[70vh] fmtm-flex fmtm-gap-10 fmtm-flex-col md:fmtm-flex-row">
      <div className="fmtm-w-full md:fmtm-w-[39rem] fmtm-bg-white fmtm-rounded-xl fmtm-p-5">
        <InputTextField
          fieldType="number"
          label=""
          onChange={(e) => {
            setSearchedTaskId(e.target.value);
          }}
          value={searchedTaskId}
          placeholder="Search by task id"
        />
        <div className="fmtm-mt-5 fmtm-h-[58vh] fmtm-overflow-y-scroll scrollbar">
          {taskLoading ? (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
              {Array.from({ length: 10 }).map((_, i) => (
                <TaskCardSkeleton key={i} />
              ))}
            </div>
          ) : filteredTaskInfo?.length > 0 ? (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
              {filteredTaskInfo?.map((task: taskSubmissionInfoType) => (
                <TaskCard key={task.task_id} task={task} />
              ))}
            </div>
          ) : (
            <div className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-justify-center fmtm-mt-10">
              <p className="fmtm-text-gray-400 fmtm-text-xl">No tasks found!</p>
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
