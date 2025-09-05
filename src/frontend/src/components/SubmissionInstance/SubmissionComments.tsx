import React from 'react';
import { useParams } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules';
import CoreModules from '@/shared/CoreModules';
import { useGetTaskEventHistoryQuery } from '@/api/task/index';

const SubmissionComments = () => {
  const params = useParams();
  const submissionInstanceId = params.instanceId;
  const taskId = params.taskId;
  const projectId = params.projectId;

  const { data: taskComments, isLoading: isTaskCommentsLoading } = useGetTaskEventHistoryQuery({
    id: +taskId!,
    params: { project_id: +projectId!, comments: true },
    options: { queryKey: ['get-task-history-comments', +projectId!] },
  });

  // handle for old project comments
  const oldfilteredTaskCommentsList =
    taskComments
      ?.filter((entry) => entry?.comment?.includes('-SUBMISSION_INST-'))
      .filter((entry) => entry?.comment?.split('-SUBMISSION_INST-')[0] === submissionInstanceId) || [];

  const newfilteredTaskCommentsList =
    taskComments?.filter((comment) => comment?.comment?.split(' ')?.[0] === `#submissionId:${submissionInstanceId}`) ||
    [];

  const filteredTaskCommentsList = [...oldfilteredTaskCommentsList, ...newfilteredTaskCommentsList];

  return (
    <div className="fmtm-bg-white fmtm-rounded-xl fmtm-p-6">
      <h4 className="fmtm-font-bold fmtm-text-[#555] fmtm-text-xl fmtm-mb-[0.625rem]">Comments</h4>
      {isTaskCommentsLoading ? (
        <div>
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-py-[0.875rem] fmtm-border-b fmtm-border-[#D4D4D4]"
            >
              <div className="fmtm-flex fmtm-justify-between">
                <CoreModules.Skeleton className="!fmtm-w-[6rem] fmtm-h-6" />
                <CoreModules.Skeleton className="!fmtm-w-[6rem] fmtm-h-4" />
              </div>
              <CoreModules.Skeleton className="!fmtm-w-full fmtm-h-5" />
            </div>
          ))}
        </div>
      ) : filteredTaskCommentsList?.length > 0 ? (
        filteredTaskCommentsList?.map((entry) => (
          <div
            key={entry?.event_id}
            className="fmtm-py-[0.875rem] fmtm-border-b fmtm-border-[#D4D4D4] fmtm-flex fmtm-flex-col fmtm-gap-2"
          >
            <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
              <p className="fmtm-text-base fmtm-font-bold fmtm-text-[#555]">{entry?.username}</p>
              <div className="fmtm-flex fmtm-items-center fmtm-gap-1">
                <AssetModules.CalendarTodayOutlinedIcon style={{ fontSize: '12px' }} className="fmtm-text-[#D73F37]" />
                <p className="fmtm-text-xs fmtm-text-[#555]">{entry?.created_at?.split('T')[0]}</p>
              </div>
            </div>
            <p className="fmtm-text-[#555] fmtm-text-sm">
              {entry?.comment?.split('-SUBMISSION_INST-')?.[1] ||
                entry?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
            </p>
          </div>
        ))
      ) : (
        <p className="fmtm-text-center fmtm-py-5 fmtm-text-xl fmtm-text-gray-400">No Comments!</p>
      )}
    </div>
  );
};

export default SubmissionComments;
