import { useQuery } from '@tanstack/react-query';
import { downloadTemplateXlsform } from '@/services/helper';
import type { TQueryOptions, xlsformTemplateDownloadParamsType } from '@/types';

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
