import React, { useEffect, useState } from 'react';
import RichTextEditor from '@/components/common/Editor/Editor';
import Button from '@/components/common/Button';
import { PostProjectComments, GetProjectComments } from '@/api/Project';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import environment from '@/environment';
import { useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { ProjectCommentsSekeletonLoader } from '@/components/ProjectDetailsV2/SkeletonLoader';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';

const Comments = () => {
  const dispatch = useDispatch();
  const params = useParams();
  const [comment, setComment] = useState('');
  const [isEditorEmpty, setIsEditorEmpty] = useState(true);
  const projectCommentsList = useAppSelector((state) => state?.project?.projectCommentsList);
  const projectGetCommentsLoading = useAppSelector((state) => state?.project?.projectGetCommentsLoading);
  const projectPostCommentsLoading = useAppSelector((state) => state?.project?.projectPostCommentsLoading);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);

  const projectId = environment.decode(params.id);

  useEffect(() => {
    dispatch(
      GetProjectComments(
        `${import.meta.env.VITE_API_URL}/tasks/task-comments/?project_id=${projectId}&task_id=${selectedTask}`,
      ),
    );
  }, [selectedTask, projectId]);

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
      PostProjectComments(`${import.meta.env.VITE_API_URL}/tasks/task-comments/`, {
        task_id: selectedTask,
        project_id: projectId,
        comment,
      }),
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
            {projectCommentsList?.length > 0 ? (
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-mb-1">
                {projectCommentsList?.map((projectComment, i) => (
                  <div key={i} className="fmtm-flex fmtm-w-full fmtm-gap-4 fmtm-px-2">
                    <div className="fmtm-h-8 fmtm-w-8 fmtm-rounded-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-bg-white">
                      <AssetModules.PersonIcon color="success" sx={{ fontSize: '30px' }} />
                    </div>
                    <div className=" fmtm-flex-1">
                      <div className="fmtm-flex fmtm-gap-3 fmtm-items-center">
                        <p>{projectComment?.commented_by}</p>
                        <p className="fmtm-text-sm fmtm-text-gray-600">
                          {projectComment?.created_at?.split('T')[0]} {projectComment?.created_at?.split('T')[1]}
                        </p>
                      </div>
                      <div className="fmtm-mt-2">
                        <RichTextEditor editorHtmlContent={projectComment?.comment} editable={false} />
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
      <div className="fmtm-pt-2">
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
            btnText="Cancel"
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
            btnText="Save Comment"
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
