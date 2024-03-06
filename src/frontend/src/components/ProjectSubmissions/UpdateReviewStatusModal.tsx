import React, { useState } from 'react';
import { Modal } from '@/components/common/Modal';
import CoreModules from '@/shared/CoreModules';
import { useDispatch } from 'react-redux';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { reviewListType } from '@/models/submission/submissionModel';
import TextArea from '../common/TextArea';
import Button from '../common/Button';

const reviewList: reviewListType[] = [
  {
    id: 'approved',
    title: 'Approved',
    className: 'fmtm-bg-[#E7F3E8] fmtm-text-[#40B449] fmtm-border-[#40B449]',
    hoverClass: 'hover:fmtm-text-[#40B449] hover:fmtm-border-[#40B449]',
  },
  {
    id: 'hasIssue',
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
  const dispatch = useDispatch();
  const [reviewStatus, setReviewStatus] = useState<string>('');
  const [noteComments, setNoteComments] = useState<string>('');
  const updateReviewStatusModal = CoreModules.useAppSelector((state) => state.submission.updateReviewStatusModal);

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
          <div className="fmtm-flex fmtm-justify-between fmtm-gap-2 fmtm-mb-4">
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
                    submissionId: null,
                  }),
                );
              }}
            />
            <Button
              btnText="Update"
              btnType="primary"
              className="fmtm-w-full fmtm-justify-center !fmtm-rounded fmtm-font-bold fmtm-text-sm !fmtm-py-2"
              onClick={() => {}}
            />
          </div>
        </div>
      }
      open={updateReviewStatusModal.toggleModalStatus}
      onOpenChange={(value) => {
        dispatch(
          SubmissionActions.SetUpdateReviewStatusModal({
            toggleModalStatus: value,
            submissionId: null,
          }),
        );
      }}
    />
  );
};

export default UpdateReviewStatusModal;
