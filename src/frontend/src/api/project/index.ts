import { useMutation, useQuery } from '@tanstack/react-query';
import { generateProjectBasemap, getProjectSummaries, getTilesList } from '@/services/project';
import { paginationType } from '@/store/types/ICommon';
import { TMutationOptions, TQueryOptions } from '@/types';
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
  options: TQueryOptions<{ results: projectSummaryType[]; pagination: paginationType }>;
}) {
  return useQuery({
    queryFn: () => getProjectSummaries(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetTilesListQuery({ id, options }: { id: number; options: TQueryOptions<tileType[]> }) {
  return useQuery({
    queryFn: () => getTilesList(id),
    select: (data) => data.data,
    ...options,
  });
}

export function useGenerateProjectBasemapMutation({
  id,
  options,
}: {
  id: number;
  options: TMutationOptions<{ Message: string }, generateProjectBasemapPayloadType>;
}) {
  return useMutation({
    mutationKey: ['generate-project-basemap', id],
    mutationFn: (payload: generateProjectBasemapPayloadType) => generateProjectBasemap(id, payload),
    ...options,
  });
}
