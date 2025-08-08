import { useMutation, useQuery } from '@tanstack/react-query';
import type { UseMutationOptions, UseQueryOptions } from '@tanstack/react-query';
import { generateProjectBasemap, getProjectSummaries, getTilesList } from '@/services/project';
import { paginationType } from '@/store/types/ICommon';
import type {
  generateProjectBasemapPayloadType,
  tileType,
  projectSummariesParamsType,
  projectSummaryType,
} from './types';

export function useGetProjectSummariesQuery({
  params,
  options,
}: {
  params: projectSummariesParamsType;
  options: UseQueryOptions<{ results: projectSummaryType[]; pagination: paginationType }>;
}) {
  return useQuery({
    queryFn: async () => (await getProjectSummaries(params)).data,
    ...options,
  });
}

export function useGetTilesListQuery({ id, options }: { id: number; options: UseQueryOptions<tileType[]> }) {
  return useQuery({
    queryFn: async () => (await getTilesList(id)).data,
    ...options,
  });
}

export function useGenerateProjectBasemapMutation({
  id,
  payload,
  options,
}: {
  id: number;
  payload: generateProjectBasemapPayloadType;
  options: UseMutationOptions;
}) {
  return useMutation({
    mutationKey: ['generate-project-basemap', id, payload],
    mutationFn: () => generateProjectBasemap(id, payload),
    ...options,
  });
}
