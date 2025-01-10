import React, { useEffect, useState } from 'react';
import { Modal } from '@/components/common/Modal';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { reviewListType } from '@/models/submission/submissionModel';
import { UpdateReviewStateService } from '@/api/SubmissionService';
import TextArea from '../common/TextArea';
import Button from '../common/Button';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { PostProjectComments } from '@/api/Project';
import { task_event } from '@/types/enums';

// Note these id values must be camelCase to match what ODK Central requires
const reviewList: reviewListType[] = [
  {
    id: 'approved',
    title: 'Approved',
    className: 'fmtm-bg-[#E7F3E8] fmtm-text-[#40B449] fmtm-border-[#40B449]',
    hoverClass: 'hover:fmtm-text-[#40B449] hover:fmtm-border-[#40B449]',
  },
  {
    id: 'hasIssues',
    title: 'Has Issue',
    className: 'fmtm-bg-[#E9DFCF] fmtm-text-[#D99F00] fmtm-border-[#D99F00]',
    hoverClass: 'hover:fmtm-text-[#D99F00] hover:fmtm-border-[#D99F00]',
  },
  {
    id: 'rejected',
    title: 'Rejected',
    className: 'fmtm-bg-[#E8D5D5] fmtm-text-[#D73F37] fmtm-border-[#D73F37]',
    hoverClass: 'hover:fmtm-text-[#D73F37] hover:fmtm-border-[#D73F37]',
  },
];

const UpdateReviewStatusModal = () => {
  const dispatch = useAppDispatch();
  const [noteComments, setNoteComments] = useState('');
  const [reviewStatus, setReviewStatus] = useState('');
  const updateReviewStatusModal = useAppSelector((state) => state.submission.updateReviewStatusModal);
  const updateReviewStateLoading = useAppSelector((state) => state.submission.updateReviewStateLoading);

  useEffect(() => {
    setReviewStatus(updateReviewStatusModal.reviewState);
  }, [updateReviewStatusModal.reviewState]);

  const handleStatusUpdate = async () => {
    if (
      !updateReviewStatusModal.instanceId ||
      !updateReviewStatusModal.projectId ||
      !updateReviewStatusModal.taskId ||
      !updateReviewStatusModal?.taskUid
    ) {
      return;
    }

    if (updateReviewStatusModal.reviewState !== reviewStatus) {
      await dispatch(
        UpdateReviewStateService(
          `${import.meta.env.VITE_API_URL}/submission/update-review-state?project_id=${updateReviewStatusModal.projectId}`,
          {
            instance_id: updateReviewStatusModal.instanceId,
            review_state: reviewStatus,
          },
        ),
      );
    }
    if (noteComments.trim().length > 0) {
      dispatch(
        PostProjectComments(
          `${import.meta.env.VITE_API_URL}/tasks/${updateReviewStatusModal?.taskUid}/event?project_id=${updateReviewStatusModal?.projectId}`,
          {
            task_id: +updateReviewStatusModal?.taskUid,
            comment: `${updateReviewStatusModal?.instanceId}-SUBMISSION_INST-${noteComments}`,
            event: task_event.COMMENT,
          },
        ),
      );
      setNoteComments('');
    }
    dispatch(
      SubmissionActions.SetUpdateReviewStatusModal({
        toggleModalStatus: false,
        projectId: null,
        instanceId: null,
        taskId: null,
        reviewState: '',
        taskUid: null,
      }),
    );
    dispatch(SubmissionActions.UpdateReviewStateLoading(false));
  };

  return (
    <Modal
      title={
        <div className="fmtm-w-full fmtm-flex fmtm-justify-start">
          <h2 className="!fmtm-text-lg fmtm-font-archivo fmtm-tracking-wide">Update Review Status</h2>
        </div>
      }
      className="!fmtm-w-fit !fmtm-outline-none fmtm-rounded-xl"
      description={
        <div className="fmtm-mt-9">
          <div className="fmtm-mb-4">
            <div className="fmtm-flex fmtm-justify-between fmtm-gap-2">
              {reviewList.map((reviewBtn) => (
                <button
                  key={reviewBtn.id}
                  className={`${
                    reviewBtn.id === reviewStatus
                      ? reviewBtn.className
                      : `fmtm-border-[#D7D7D7] fmtm-bg-[#F5F5F5] fmtm-text-[#484848] ${reviewBtn.hoverClass} fmtm-duration-150`
                  } fmtm-pt-2 fmtm-pb-1 fmtm-px-7 fmtm-outline-none fmtm-w-fit fmtm-border-[1px] fmtm-rounded-[40px] fmtm-font-archivo fmtm-text-sm`}
                  onClick={() => setReviewStatus(reviewBtn.id)}
                >
                  {reviewBtn.title}
                </button>
              ))}
            </div>
          </div>
          <TextArea
            rows={4}
            onChange={(e) => setNoteComments(e.target.value)}
            value={noteComments}
            label="Note & Comments"
          />
          <div className="fmtm-grid fmtm-grid-cols-2 fmtm-gap-4 fmtm-mt-8">
            <Button
              btnText="Cancel"
              btnType="other"
              className="fmtm-w-full fmtm-justify-center !fmtm-rounded fmtm-font-bold fmtm-text-sm !fmtm-py-2"
              onClick={() => {
                dispatch(
                  SubmissionActions.SetUpdateReviewStatusModal({
                    toggleModalStatus: false,
                    projectId: null,
                    instanceId: null,
                    taskId: null,
                    reviewState: '',
                    taskUid: null,
                  }),
                );
              }}
            />
            <Button
              loadingText="Updating"
              isLoading={updateReviewStateLoading}
              disabled={!reviewStatus}
              btnText="Update"
              btnType="primary"
              className="fmtm-w-full fmtm-justify-center !fmtm-rounded fmtm-font-bold fmtm-text-sm !fmtm-py-2"
              onClick={handleStatusUpdate}
            />
          </div>
        </div>
      }
      open={updateReviewStatusModal.toggleModalStatus}
      onOpenChange={(value) => {
        dispatch(
          SubmissionActions.SetUpdateReviewStatusModal({
            toggleModalStatus: value,
            projectId: null,
            instanceId: null,
            taskId: null,
            reviewState: '',
            taskUid: null,
          }),
        );
      }}
    />
  );
};

export default UpdateReviewStatusModal;
