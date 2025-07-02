import React, { useEffect, useState } from 'react';
import RichTextEditor from '@/components/common/Editor/Editor';
import Button from '@/components/common/Button';
import { PostProjectComments, GetProjectComments } from '@/api/Project';
import { useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import ProjectCommentsSekeleton from '@/components/Skeletons/ProjectDetails/ProjectCommentsSekeleton';
import { project_status } from '@/types/enums';

type propType = {
  projectStatus: project_status;
};

const Comments = ({ projectStatus }: propType) => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const projectId: any = params.id;

  const [comment, setComment] = useState('');
  const [isEditorEmpty, setIsEditorEmpty] = useState(true);
  const projectCommentsList = useAppSelector((state) => state?.project?.projectCommentsList);
  const projectGetCommentsLoading = useAppSelector((state) => state?.project?.projectGetCommentsLoading);
  const projectPostCommentsLoading = useAppSelector((state) => state?.project?.projectPostCommentsLoading);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == +projectId);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.id == selectedTask;
    })?.[0],
  };
  // filter out submission/feature level comments
  const filteredProjectCommentsList = projectCommentsList?.filter(
    (entry) => !entry?.comment?.includes('-SUBMISSION_INST-') && !entry?.comment?.startsWith('#submissionId:uuid:'),
  );

  useEffect(() => {
    dispatch(
      GetProjectComments(
        `${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/history?project_id=${projectId}&comments=true`,
      ),
    );
  }, [selectedTask, projectId, currentStatus?.id]);

  const clearComment = () => {
    dispatch(ProjectActions.ClearEditorContent(true));
    setComment('');
  };

  const handleComment = () => {
    if (isEditorEmpty) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Empty comment field.',
        }),
      );
      return;
    }
    dispatch(
      PostProjectComments(`${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/event?project_id=${projectId}`, {
        task_id: selectedTask.id,
        comment,
      }),
    );
    clearComment();
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-w-full fmtm-h-full sm:fmtm-h-[calc(100%-54px)] fmtm-z-50">
      <div className="fmtm-flex-1 fmtm-overflow-y-scroll scrollbar">
        {projectGetCommentsLoading ? (
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-mb-1">
            {Array.from({ length: 8 }).map((_, i) => (
              <ProjectCommentsSekeleton key={i} />
            ))}
          </div>
        ) : (
          <div>
            {filteredProjectCommentsList?.length > 0 ? (
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-mb-1">
                {filteredProjectCommentsList?.map((commentEvent, i) => (
                  <div
                    key={i}
                    className="fmtm-flex fmtm-w-full fmtm-gap-4 fmtm-px-2 fmtm-border-b fmtm-border-[#e9e9e9] sm:fmtm-border-white fmtm-pb-3"
                  >
                    <div className="fmtm-h-8 fmtm-w-8 fmtm-rounded-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-bg-white">
                      <AssetModules.PersonIcon color="success" sx={{ fontSize: '30px' }} />
                    </div>
                    <div className="fmtm-flex-1 fmtm-flex fmtm-flex-col fmtm-gap-1">
                      <div className="fmtm-flex fmtm-gap-3 fmtm-items-center">
                        <p>{commentEvent?.username}</p>
                      </div>
                      <div>
                        <RichTextEditor
                          editorHtmlContent={commentEvent?.comment}
                          editable={false}
                          className="sm:!fmtm-bg-grey-100 !fmtm-rounded-none !fmtm-border-none"
                        />
                      </div>
                      <div className="fmtm-flex fmtm-items-center fmtm-justify-between">
                        <p className="fmtm-text-sm fmtm-text-[#7A7676]">#{selectedTask}</p>
                        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
                          <AssetModules.AccessTimeIcon className="fmtm-text-primaryRed" style={{ fontSize: '20px' }} />
                          <p className="fmtm-text-sm fmtm-text-[#7A7676] fmtm-flex fmtm-gap-2">
                            <span>{commentEvent?.created_at?.split('T')[0]}</span>
                            <span>
                              {commentEvent?.created_at?.split('T')[1].split(':')[0]}:
                              {commentEvent?.created_at?.split('T')[1].split(':')[1]}
                            </span>
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="fmtm-mt-5 fmtm-text-center fmtm-text-xl fmtm-text-gray-400">No Comments!</p>
            )}
          </div>
        )}
      </div>
      {projectStatus === project_status.PUBLISHED && (
        <div className="fmtm-pt-2">
          <RichTextEditor
            editorHtmlContent={comment}
            setEditorHtmlContent={(content) => setComment(content)}
            editable={true}
            isEditorEmpty={(status) => setIsEditorEmpty(status)}
            className="sm:fmtm-h-[235px] fmtm-overflow-scroll scrollbar"
          />
          <div className="fmtm-mt-2 fmtm-w-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-gap-4">
            <Button
              variant="secondary-grey"
              onClick={() => {
                clearComment();
                dispatch(ProjectActions.SetMobileFooterSelection(''));
              }}
              className="!fmtm-w-1/2"
            >
              Clear Comment
            </Button>
            <Button
              variant="primary-grey"
              onClick={handleComment}
              className="!fmtm-w-1/2"
              isLoading={projectPostCommentsLoading}
            >
              Save Comment
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Comments;
