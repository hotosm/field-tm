import React, { useEffect, useState } from 'react';
import RichTextEditor from '@/components/common/Editor/Editor';
import Button from '@/components/common/Button';
import { PostProjectComments, GetProjectComments } from '@/api/Project';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { ProjectCommentsSekeletonLoader } from '@/components/ProjectDetailsV2/SkeletonLoader';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';

const Comments = () => {
  const dispatch = useDispatch();
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
  const taskBoundaryData = useAppSelector((state) => state.project.projectTaskBoundries);
  const currentStatus = {
    ...taskBoundaryData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task?.id == selectedTask;
    })?.[0],
  };
  const filteredProjectCommentsList = projectCommentsList?.filter(
    (comment) => !comment?.action_text?.includes('-SUBMISSION_INST-'),
  );

  useEffect(() => {
    console.log(currentStatus);
    dispatch(
      GetProjectComments(
        `${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/history/?project_id=${projectId}&comment=true`,
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
          open: true,
          message: 'Empty comment field.',
          variant: 'error',
          duration: 2000,
        }),
      );
      return;
    }
    dispatch(
      PostProjectComments(
        `${import.meta.env.VITE_API_URL}/tasks/${currentStatus?.id}/comment/?project_id=${projectId}`,
        {
          comment,
        },
      ),
    );
    clearComment();
  };

  return (
    <div style={{ height: 'calc(100% - 120px)' }} className="fmtm-w-full fmtm-z-50">
      <div style={{ height: 'calc(100% - 271px)' }} className="fmtm-overflow-y-scroll scrollbar">
        {projectGetCommentsLoading ? (
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-mb-1">
            {Array.from({ length: 8 }).map((_, i) => (
              <ProjectCommentsSekeletonLoader key={i} />
            ))}
          </div>
        ) : (
          <div>
            {filteredProjectCommentsList?.length > 0 ? (
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-mb-1">
                {filteredProjectCommentsList?.map((projectComment, i) => (
                  <div
                    key={i}
                    className="fmtm-flex fmtm-w-full fmtm-gap-4 fmtm-px-2 fmtm-border-b fmtm-border-[#e9e9e9] sm:fmtm-border-white fmtm-pb-3"
                  >
                    <div className="fmtm-h-8 fmtm-w-8 fmtm-rounded-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-bg-white">
                      <AssetModules.PersonIcon color="success" sx={{ fontSize: '30px' }} />
                    </div>
                    <div className="fmtm-flex-1 fmtm-flex fmtm-flex-col fmtm-gap-1">
                      <div className="fmtm-flex fmtm-gap-3 fmtm-items-center">
                        <p>{projectComment?.username}</p>
                      </div>
                      <div>
                        <RichTextEditor
                          editorHtmlContent={projectComment?.action_text}
                          editable={false}
                          className="sm:!fmtm-bg-[#f5f5f5] !fmtm-rounded-none !fmtm-border-none"
                        />
                      </div>
                      <div className="fmtm-flex fmtm-items-center fmtm-justify-between">
                        <p className="fmtm-font-archivo fmtm-text-sm fmtm-text-[#7A7676]">#{selectedTask}</p>
                        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
                          <div className="fmtm-flex fmtm-items-center fmtm-mb-1">
                            <AssetModules.AccessTimeIcon
                              className="fmtm-text-primaryRed"
                              style={{ fontSize: '20px' }}
                            />
                          </div>
                          <p className="fmtm-font-archivo fmtm-text-sm fmtm-text-[#7A7676] fmtm-flex fmtm-gap-2">
                            <span>{projectComment?.action_date?.split('T')[0]}</span>
                            <span>
                              {projectComment?.action_date?.split('T')[1].split(':')[0]}:
                              {projectComment?.action_date?.split('T')[1].split(':')[1]}
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
      <div className="fmtm-pt-2 sm:fmtm-max-h-[235px] sm:fmtm-overflow-scroll sm:scrollbar">
        <RichTextEditor
          editorHtmlContent={comment}
          setEditorHtmlContent={(content) => setComment(content)}
          editable={true}
          isEditorEmpty={(status) => setIsEditorEmpty(status)}
        />
      </div>
      <div className="fmtm-mt-4 fmtm-w-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-gap-4">
        <div className="fmtm-w-1/2">
          <Button
            type="button"
            btnText="CLEAR COMMENT"
            btnType="other"
            className="!fmtm-rounded !fmtm-py-[3px] fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={() => {
              clearComment();
              dispatch(ProjectActions.SetMobileFooterSelection(''));
            }}
          />
        </div>
        <div className="fmtm-w-1/2">
          <Button
            type="button"
            btnText="SAVE COMMENT"
            btnType="primary"
            className="!fmtm-rounded fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={handleComment}
            isLoading={projectPostCommentsLoading}
            loadingText="Saving..."
          />
        </div>
      </div>
    </div>
  );
};

export default Comments;
