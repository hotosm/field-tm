import React, { useEffect, useState } from 'react';
import type { AxiosResponse } from 'axios';
import { useQueryClient } from '@tanstack/react-query';
import Mentions from 'rc-mentions';
import '@/styles/rc-mentions.css';
import { Modal } from '@/components/common/Modal';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { reviewListType } from '@/models/submission/submissionModel';
import Button from '@/components/common/Button';
import { entity_state } from '@/types/enums';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { task_event } from '@/types/enums';
import { useUpdateReviewStateMutation } from '@/api/submission';
import { useSetEntitiesMappingStatusMutation } from '@/api/project';
import { useAddNewTaskEventMutation } from '@/api/task/index';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useGetUserListQuery } from '@/api/user';
import type { taskEventType } from '@/types';

const initialReviewState = {
  toggleModalStatus: false,
  projectId: null,
  instanceId: null,
  taskId: null,
  reviewState: '',
  taskUid: null,
  entity_id: null,
  label: null,
};

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
];

const UpdateReviewStatusModal = () => {
  const dispatch = useAppDispatch();
  const { Option } = Mentions;
  const queryClient = useQueryClient();

  const [noteComments, setNoteComments] = useState('');
  const [reviewStatus, setReviewStatus] = useState('');
  const [searchText, setSearchText] = useState('');

  const updateReviewStatusModal = useAppSelector((state) => state.submission.updateReviewStatusModal);

  const { mutate: setEntitiesMappingStatusMutate, isPending: isSetEntitiesMappingStatusPending } =
    useSetEntitiesMappingStatusMutation({
      project_id: updateReviewStatusModal.projectId!,
      options: {
        onSuccess: () => {
          dispatch(CommonActions.SetSnackBar({ message: 'Review state updated successfully', variant: 'success' }));
        },
        onError: (error) => {
          dispatch(
            CommonActions.SetSnackBar({
              message: error?.response?.data?.detail || 'Failed to update entity mapping status',
            }),
          );
        },
      },
    });

  const { isPending: isUpdateReviewStatePending, mutateAsync: updateReviewStateMutateAsync } =
    useUpdateReviewStateMutation({
      params: { project_id: +updateReviewStatusModal.projectId! },
      options: {
        onSuccess: ({ data }) => {
          setEntitiesMappingStatusMutate({
            entity_id: updateReviewStatusModal.entity_id!,
            status: reviewStatus === 'approved' ? entity_state['VALIDATED'] : entity_state['MARKED_BAD'],
            label: updateReviewStatusModal.label as string,
          });
          queryClient.setQueryData<AxiosResponse<Record<string, any>>>(
            ['get-project-submission-detail', +updateReviewStatusModal.projectId!, updateReviewStatusModal.instanceId],
            (prevData) => {
              if (!prevData) return prevData;
              return {
                ...prevData,
                data: {
                  ...prevData.data,
                  __system: {
                    ...prevData.data.__system,
                    updatedAt: data.updatedAt,
                    reviewState: data.reviewState,
                    deviceId: data.deviceId,
                  },
                },
              };
            },
          );
        },
        onError: (error) => {
          dispatch(
            CommonActions.SetSnackBar({
              message: error?.response?.data?.detail || 'Failed to update review state',
            }),
          );
        },
      },
    });

  // post submission instance comments
  const { isPending: isAddNewTaskEventPending, mutateAsync: addNewTaskEventMutateAsync } = useAddNewTaskEventMutation({
    id: +updateReviewStatusModal?.taskUid!,
    options: {
      onSuccess: ({ data }) => {
        setNoteComments('');

        queryClient.setQueryData<AxiosResponse<taskEventType[]>>(
          ['get-project-comments', +updateReviewStatusModal.projectId!],
          (prevData) => {
            if (!prevData) return prevData;
            return {
              ...prevData,
              data: [data, ...prevData.data],
            };
          },
        );
      },
      onError: (error) => {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Failed to add comment',
          }),
        );
      },
    },
  });

  const {
    data: userList,
    isLoading: isUserListLoading,
    refetch: getUserList,
  } = useGetUserListQuery({
    params: { search: searchText },
    options: {
      queryKey: ['get-user-list', searchText],
      enabled: false,
    },
  });

  useEffect(() => {
    if (!updateReviewStatusModal.projectId) return;

    const timeoutId = setTimeout(() => {
      if (!updateReviewStatusModal.projectId) return;
      getUserList();
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchText]);

  useEffect(() => {
    setReviewStatus(updateReviewStatusModal.reviewState);
  }, [updateReviewStatusModal.reviewState]);

  const handleStatusUpdate = async () => {
    if (
      !updateReviewStatusModal.instanceId ||
      !updateReviewStatusModal.projectId ||
      !updateReviewStatusModal.taskId ||
      !updateReviewStatusModal.entity_id ||
      !updateReviewStatusModal.taskUid
    ) {
      return;
    }

    const promises: Promise<any>[] = [];

    if (updateReviewStatusModal.reviewState !== reviewStatus) {
      promises.push(
        updateReviewStateMutateAsync({
          instance_id: updateReviewStatusModal.instanceId,
          review_state: reviewStatus,
        }),
      );
    }

    if (noteComments.trim().length > 0) {
      promises.push(
        addNewTaskEventMutateAsync({
          payload: {
            task_id: +updateReviewStatusModal?.taskUid,
            comment: `#submissionId:${updateReviewStatusModal?.instanceId} #featureId:${updateReviewStatusModal?.entity_id} ${noteComments}`,
            event: task_event.COMMENT,
          },
          params: {
            project_id: +updateReviewStatusModal.projectId,
          },
        }),
      );
    }

    try {
      await Promise.all(promises);
      dispatch(SubmissionActions.SetUpdateReviewStatusModal(initialReviewState));
    } catch (err) {
      dispatch(CommonActions.SetSnackBar({ message: 'There was an error updating the status' }));
    }
  };

  return (
    <Modal
      title={
        <div className="fmtm-w-full fmtm-flex fmtm-justify-start">
          <h2 className="!fmtm-text-lg fmtm-font-archivo fmtm-tracking-wide">Update Review Status</h2>
        </div>
      }
      className="!fmtm-w-[23rem] !fmtm-outline-none fmtm-rounded-xl"
      description={
        <div className="fmtm-mt-9">
          <div className="fmtm-flex fmtm-gap-2 fmtm-mb-4">
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
          <div>
            <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold">Note & Comments</p>
            <Mentions
              value={noteComments}
              onChange={setNoteComments}
              onSearch={(search) => {
                setSearchText(search);
              }}
              notFoundContent={isUserListLoading ? 'Searching...' : searchText ? 'Search for a user' : 'User not found'}
            >
              {userList?.map((user) => (
                <Option key={user.sub} value={user.username}>
                  {user.username}
                </Option>
              ))}
            </Mentions>
          </div>
          <div className="fmtm-grid fmtm-grid-cols-2 fmtm-gap-4 fmtm-mt-8">
            <Button
              variant="secondary-red"
              onClick={() => {
                dispatch(SubmissionActions.SetUpdateReviewStatusModal(initialReviewState));
              }}
              className="!fmtm-w-full"
            >
              Cancel
            </Button>
            <Button
              variant="primary-red"
              onClick={handleStatusUpdate}
              isLoading={isUpdateReviewStatePending || isSetEntitiesMappingStatusPending || isAddNewTaskEventPending}
              disabled={!reviewStatus}
              className="!fmtm-w-full"
            >
              Update
            </Button>
          </div>
        </div>
      }
      open={updateReviewStatusModal.toggleModalStatus}
      onOpenChange={(value) => {
        dispatch(
          SubmissionActions.SetUpdateReviewStatusModal({
            ...initialReviewState,
            toggleModalStatus: value,
          }),
        );
      }}
    />
  );
};

export default UpdateReviewStatusModal;
