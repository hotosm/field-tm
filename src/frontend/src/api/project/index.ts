import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { getProjectSummaries } from '@/services/project';

type ProjectSummariesResponse = { results: Record<string, any>[]; pagination: Record<string, any> };

export function useGetProjectSummaries({
  params,
  queryOptions,
}: {
  params: Record<string, any>;
  queryOptions: UseQueryOptions<ProjectSummariesResponse>;
}) {
  return useQuery({
    queryFn: async () => (await getProjectSummaries(params)).data,
    ...queryOptions,
  });
}
