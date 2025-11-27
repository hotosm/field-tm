import { useQuery, useMutation } from '@tanstack/react-query';
import {
  testOdkCredentials,
  getFormLists,
  uploadProjectXlsform,
  updateProjectForm,
  downloadForm,
  detectFormLanguages,
} from '@/services/central';
import type { TQueryOptions, TMutationOptions, odkCredsParamsType } from '@/types';
import type { formLanguagesType, formType, updateProjectFormPayloadType, uploadXlsformParamsType } from './types';

export function useTestOdkCredentialsMutation(
  options: TMutationOptions<void, { params: odkCredsParamsType }, { detail: string }>,
) {
  return useMutation({
    mutationFn: ({ params }) => testOdkCredentials(params),
    ...options,
  });
}

export function useGetFormListsQuery({ options }: { options: TQueryOptions<formType[]> }) {
  return useQuery({
    queryFn: () => getFormLists(),
    select: (data) => data.data,
    ...options,
  });
}

export function useDownloadFormQuery({
  params,
  options,
}: {
  params: { project_id: number };
  options: TQueryOptions<Blob, Blob>;
}) {
  return useQuery({
    queryFn: () => downloadForm(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useUploadProjectXlsformMutation(
  options: TMutationOptions<
    { message: string },
    { payload: FormData; params: uploadXlsformParamsType },
    { detail: string }
  >,
) {
  return useMutation({
    mutationFn: ({ payload, params }) => uploadProjectXlsform(payload, params),
    ...options,
  });
}

export function useUpdateProjectFormMutation({
  params,
  options,
}: {
  params: { project_id: number };
  options: TMutationOptions<unknown, updateProjectFormPayloadType>;
}) {
  return useMutation({
    mutationKey: ['update-form'],
    mutationFn: (payload: updateProjectFormPayloadType) => updateProjectForm(payload, params),
    ...options,
  });
}

export function useDetectFormLanguagesMutation(
  options: TMutationOptions<formLanguagesType, { payload: FormData }, { message: string }>,
) {
  return useMutation({
    mutationFn: ({ payload }) => detectFormLanguages(payload),
    ...options,
  });
}
