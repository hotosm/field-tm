import { useQuery } from '@tanstack/react-query';
import { downloadTemplateXlsform, getMetrics } from '@/services/helper';
import type { metricsType, TQueryOptions, xlsformTemplateDownloadParamsType } from '@/types';

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

export function useGetMetricsQuery({ options }: { options: TQueryOptions<metricsType> }) {
  return useQuery({
    queryFn: () => getMetrics(),
    select: (data) => data.data,
    ...options,
  });
}
