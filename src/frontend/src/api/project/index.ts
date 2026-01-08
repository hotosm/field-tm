import { useMutation, useQuery } from '@tanstack/react-query';
import {
  generateProjectBasemap,
  getProjectSummaries,
  getTilesList,
  patchCreateProject,
  getOdkEntitiesGeojson,
  getOdkEntitiesMappingStatuses,
  downloadFeatures,
  getContributors,
  taskSplit,
  previewSplitBySquare,
  generateDataExtract,
  uploadDataExtract,
  addProjectManager,
  getProjectUsers,
  generateFiles,
  getProject,
  updateProject,
  deleteProject,
  uploadProjectTaskBoundaries,
  createStubProject,
  downloadProjectBoundary,
  downloadTaskBoundaries,
  deleteEntity,
  unassignUserFromProject,
  setEntitiesMappingStatus,
} from '@/services/project';
import { paginationType } from '@/store/types/ICommon';
import { TMutationOptions, TQueryOptions } from '@/types';
import type {
  generateProjectBasemapPayloadType,
  tileType,
  projectSummariesParamsType,
  projectSummaryType,
  odkEntitiesGeojsonParamsType,
  downloadFeaturesParamsType,
  projectUsersParamsType,
  addProjectManagerParamsType,
  projectType,
  createProjectPayloadType,
  createStubProjectParamsType,
  createStubProjectPayloadType,
  generateDataExtractPayloadType,
  uploadDataExtractPayloadType,
  taskSplitPayloadType,
  previewSplitBySquarePayload,
  odkEntitiesGeojsonType,
  odkEntitiesMappingStatusesType,
  contributorsType,
  uploadProjectTaskBoundariesPayloadType,
  updateProjectPayloadType,
  projectUserType,
  entitiesMappingStatusPayloadType,
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

export const usePatchCreateProjectMutation = ({
  params,
  options,
}: {
  params: { project_id: number };
  options: TMutationOptions<any, createProjectPayloadType>;
}) =>
  useMutation({
    mutationFn: (payload: createProjectPayloadType) => patchCreateProject(payload, params),
    ...options,
  });

export const useGetOdkEntitiesGeojsonQuery = (
  id: number,
  params: odkEntitiesGeojsonParamsType,
  options: TQueryOptions<odkEntitiesGeojsonType>,
) =>
  useQuery({
    queryFn: () => getOdkEntitiesGeojson(id, params),
    ...options,
  });

export const useGetOdkEntitiesMappingStatusesQuery = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TQueryOptions<odkEntitiesMappingStatusesType[]>;
}) =>
  useQuery({
    queryFn: () => getOdkEntitiesMappingStatuses(project_id),
    ...options,
  });

export const useDownloadFeaturesQuery = ({
  params,
  options,
}: {
  params: downloadFeaturesParamsType;
  options: TQueryOptions<Blob, Blob>;
}) =>
  useQuery({
    queryFn: () => downloadFeatures(params),
    select: (data) => data.data,
    ...options,
  });

export const useGetContributorsQuery = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TQueryOptions<contributorsType[]>;
}) =>
  useQuery({
    queryFn: () => getContributors(project_id),
    ...options,
  });

export const useTaskSplitMutation = (options: TMutationOptions<any, { payload: FormData }>) =>
  useMutation({
    mutationFn: ({ payload }) => taskSplit(payload),
    ...options,
  });

export const usePreviewSplitBySquareMutation = (options: TMutationOptions<any, { payload: FormData }>) =>
  useMutation({
    mutationFn: ({ payload }) => previewSplitBySquare(payload),
    ...options,
  });

export const useGenerateDataExtractMutation = (
  options: TMutationOptions<{ url: string }, { payload: FormData; params: { project_id: number } }, { detail: string }>,
) =>
  useMutation({
    mutationFn: ({ payload, params }) => generateDataExtract(payload, params),
    ...options,
  });

export const useUploadDataExtractMutation = ({
  params,
  options,
}: {
  params: { project_id: number };
  options: TMutationOptions<any, uploadDataExtractPayloadType>;
}) =>
  useMutation({
    mutationFn: (payload: uploadDataExtractPayloadType) => uploadDataExtract(payload, params),
    ...options,
  });

export const useAddProjectManagerMutation = ({ options }: { options: TMutationOptions<any, any> }) =>
  useMutation({
    mutationFn: (params: addProjectManagerParamsType) => addProjectManager(params),
    ...options,
  });

export const useGetProjectUsersQuery = ({
  project_id,
  params,
  options,
}: {
  project_id: number;
  params: projectUsersParamsType;
  options: TQueryOptions<projectUserType[]>;
}) =>
  useQuery({
    queryFn: () => getProjectUsers(project_id, params),
    select: (data) => data.data,
    ...options,
  });

export const useGenerateFilesMutation = ({ options }: { options: TMutationOptions<any, any> }) =>
  useMutation({
    mutationFn: ({ id, payload }: any) => generateFiles(id, payload),
    ...options,
  });

export const useGetProjectQuery = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TQueryOptions<projectType>;
}) =>
  useQuery({
    queryFn: () => getProject(project_id),
    select: (data) => data.data,
    ...options,
  });

export const useUpdateProjectMutation = ({
  id,
  options,
}: {
  id: number;
  options: TMutationOptions<projectType, updateProjectPayloadType>;
}) =>
  useMutation({
    mutationFn: (payload: updateProjectPayloadType) => updateProject(id, payload),
    ...options,
  });

export const useDeleteProjectMutation = (options: TMutationOptions<any, { project_id: number }>) =>
  useMutation({
    mutationFn: ({ project_id }) => deleteProject(project_id),
    ...options,
  });

export const useUploadProjectTaskBoundariesMutation = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TMutationOptions<any, uploadProjectTaskBoundariesPayloadType>;
}) =>
  useMutation({
    mutationFn: (payload: uploadProjectTaskBoundariesPayloadType) => uploadProjectTaskBoundaries(project_id, payload),
    ...options,
  });

export const useCreateStubProjectMutation = ({
  params,
  options,
}: {
  params: createStubProjectParamsType;
  options: TMutationOptions<any, createStubProjectPayloadType>;
}) =>
  useMutation({
    mutationFn: (payload: createStubProjectPayloadType) => createStubProject(payload, params),
    ...options,
  });

export const useDownloadProjectBoundaryQuery = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TQueryOptions<unknown>;
}) =>
  useQuery({
    queryFn: () => downloadProjectBoundary(project_id),
    ...options,
  });

export const useDownloadTaskBoundariesQuery = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TQueryOptions<Blob, Blob>;
}) =>
  useQuery({
    queryFn: () => downloadTaskBoundaries(project_id),
    select: (data) => data.data,
    ...options,
  });

export const useDeleteEntityMutation = ({
  entity_uuid,
  params,
  options,
}: {
  entity_uuid: string;
  params: { project_id: number };
  options: TMutationOptions<{ details: string }, void>;
}) =>
  useMutation({
    mutationFn: () => deleteEntity(entity_uuid, params),
    ...options,
  });

export const useUnassignUserFromProjectMutation = ({
  project_id,
  user_sub,
  options,
}: {
  project_id: number;
  user_sub: string;
  options: TMutationOptions<any, void>;
}) =>
  useMutation({
    mutationFn: () => unassignUserFromProject(project_id, user_sub),
    ...options,
  });

export const useSetEntitiesMappingStatusMutation = ({
  project_id,
  options,
}: {
  project_id: number;
  options: TMutationOptions<odkEntitiesMappingStatusesType, entitiesMappingStatusPayloadType, { detail: string }>;
}) =>
  useMutation({
    mutationFn: (payload) => setEntitiesMappingStatus(project_id, payload),
    ...options,
  });
