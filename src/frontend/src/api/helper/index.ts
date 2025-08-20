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

export function useTestOdkCredentialsMutation({
  params,
  options,
}: {
  params: odkCredsParamsType;
  options: TMutationOptions<unknown, void>;
}) {
  return useMutation({
    mutationKey: ['test-odk-credentials', params],
    mutationFn: () => testOdkCredentials(params),
    ...options,
  });
}
