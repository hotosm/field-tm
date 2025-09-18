import { useQuery, useMutation } from '@tanstack/react-query';
import { getFormLists, uploadProjectXlsform, updateProjectForm, downloadForm } from '@/services/central';
import type { TQueryOptions, TMutationOptions } from '@/types';
import type {
  formType,
  updateProjectFormPayloadType,
  uploadXlsformParamsType,
  uploadXlsformPayloadType,
} from './types';

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
  options: TQueryOptions<Blob>;
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
    { message: string }
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
