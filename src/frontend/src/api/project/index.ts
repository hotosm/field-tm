import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { getProjectSummaries } from '@/services/project';
import { paginationType } from '@/store/types/ICommon';
import type { projectSummariesParamsType, projectSummaryType } from './types';

export function useGetProjectSummaries({
  params,
  queryOptions,
}: {
  params: projectSummariesParamsType;
  queryOptions: UseQueryOptions<{ results: projectSummaryType[]; pagination: paginationType }>;
}) {
  return useQuery({
    queryFn: async () => (await getProjectSummaries(params)).data,
    ...queryOptions,
  });
}
