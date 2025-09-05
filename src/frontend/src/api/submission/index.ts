import { useMutation, useQuery } from '@tanstack/react-query';
import {
  getSubmissionFormFields,
  getSubmissions,
  getSubmissionTable,
  downloadSubmission,
  updateReviewState,
  getSubmissionPhotos,
  getProjectSubmissionDashboard,
  getSubmissionDetail,
} from '@/services/submission';
import type { TMutationOptions, TQueryOptions } from '@/types';
import type {
  downloadSubmissionParamsType,
  projectSubmissionDashboardType,
  submissionFormFieldsType,
  submissionsParamsType,
  submissionTableParamsType,
  submissionTableType,
  updateReviewStatePayloadType,
  updateReviewStateType,
} from './types';

export function useGetSubmissionsQuery({
  params,
  options,
}: {
  params: submissionsParamsType;
  options: TQueryOptions<Record<string, any>>;
}) {
  return useQuery({
    queryFn: () => getSubmissions(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetDownloadSubmissionQuery({
  params,
  options,
}: {
  params: downloadSubmissionParamsType;
  options: TQueryOptions<Blob, Blob>;
}) {
  return useQuery({
    queryFn: () => downloadSubmission(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetSubmissionFormFieldsQuery({
  params,
  options,
}: {
  params: { project_id: number };
  options: TQueryOptions<submissionFormFieldsType>;
}) {
  return useQuery({
    queryFn: () => getSubmissionFormFields(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetSubmissionTableQuery({
  params,
  options,
}: {
  params: submissionTableParamsType;
  options: TQueryOptions<submissionTableType>;
}) {
  return useQuery({
    queryFn: () => getSubmissionTable(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useUpdateReviewStateMutation({
  params,
  options,
}: {
  params: { project_id: number };
  options: TMutationOptions<updateReviewStateType, updateReviewStatePayloadType>;
}) {
  return useMutation({
    mutationKey: ['update-review-state', params],
    mutationFn: (payload: updateReviewStatePayloadType) => updateReviewState(params, payload),
    ...options,
  });
}

export function useGetSubmissionPhotosQuery({
  id,
  params,
  options,
}: {
  id: string;
  params: { project_id: number };
  options: TQueryOptions<Record<string, any>>;
}) {
  return useQuery({
    queryFn: () => getSubmissionPhotos(id, params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetProjectSubmissionDashboardQuery({
  id,
  options,
}: {
  id: number;
  options: TQueryOptions<projectSubmissionDashboardType>;
}) {
  return useQuery({
    queryFn: () => getProjectSubmissionDashboard(id),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetSubmissionDetailQuery({
  id,
  params,
  options,
}: {
  id: string;
  params: { project_id: number };
  options: TQueryOptions<Record<string, any>>;
}) {
  return useQuery({
    queryFn: () => getSubmissionDetail(id, params),
    select: (data) => data.data,
    ...options,
  });
}
