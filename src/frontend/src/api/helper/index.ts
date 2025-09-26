import { useQuery, useMutation } from '@tanstack/react-query';
import { testOdkCredentials, downloadTemplateXlsform } from '@/services/helper';
import type { TQueryOptions, TMutationOptions, odkCredsParamsType, xlsformTemplateDownloadParamsType } from '@/types';

export function useDownloadTemplateXlsformQuery({
  params,
  options,
}: {
  params: xlsformTemplateDownloadParamsType;
  options: TQueryOptions<Blob>;
}) {
  return useQuery({
    queryFn: () => downloadTemplateXlsform(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useTestOdkCredentialsMutation(
  options: TMutationOptions<void, { params: odkCredsParamsType }, { detail: string }>,
) {
  return useMutation({
    mutationFn: ({ params }) => testOdkCredentials(params),
    ...options,
  });
}
