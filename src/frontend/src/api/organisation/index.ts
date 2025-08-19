import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getOrganisations,
  createOrganisation,
  getMyOrganisations,
  getUnapprovedOrganisations,
  deleteUnapprovedOrganisation,
  approveOrganisation,
  addNewOrganisationAdmin,
  getOrganisationAdmins,
  getOrganisationDetail,
  updateOrganisation,
  deleteOrganisation,
  removeOrganisationAdmin,
} from '@/services/organisation';
import type { TQueryOptions, TMutationOptions } from '@/types';
import type {
  organisationType,
  organisationAdminType,
  createUpdateOrganisationPayloadType,
  approveOrganisationParamsType,
  createOrganisationParamsType,
  addNewOrganisationAdminParamsType,
  updateOrganisationParamsType,
  removeOrganisationAdminParamsType,
} from './types';

export function useGetOrganisationsQuery({ options }: { options: TQueryOptions<organisationType[]> }) {
  return useQuery({
    queryFn: () => getOrganisations(),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetMyOrganisationsQuery({ options }: { options: TQueryOptions<organisationType[]> }) {
  return useQuery({
    queryFn: () => getMyOrganisations(),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetUnapprovedOrganisationsQuery({ options }: { options: TQueryOptions<organisationType[]> }) {
  return useQuery({
    queryFn: () => getUnapprovedOrganisations(),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetOrganisationAdminsQuery({
  params,
  options,
}: {
  params: { org_id: number };
  options: TQueryOptions<organisationAdminType[]>;
}) {
  return useQuery({
    queryFn: () => getOrganisationAdmins(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetOrganisationDetailQuery({
  org_id,
  params,
  options,
}: {
  org_id: number;
  params: { org_id: number };
  options: TQueryOptions<organisationType>;
}) {
  return useQuery({
    queryFn: () => getOrganisationDetail(org_id, params),
    select: (data) => data.data,
    ...options,
  });
}

export function useCreateOrganisationMutation({
  params,
  options,
}: {
  params: createOrganisationParamsType;
  options: TMutationOptions<organisationType, createUpdateOrganisationPayloadType>;
}) {
  return useMutation({
    mutationKey: ['create-organisation', params],
    mutationFn: (payload: createUpdateOrganisationPayloadType) => createOrganisation(payload, params),
    ...options,
  });
}

export function useDeleteUnapprovedOrganisationMutation({ options }: { options: TMutationOptions<unknown, number> }) {
  return useMutation({
    mutationKey: ['delete-unapproved-organisation'],
    mutationFn: (id: number) => deleteUnapprovedOrganisation(id),
    ...options,
  });
}

export function useApproveOrganisationMutation({
  options,
  params,
}: {
  params: approveOrganisationParamsType;
  options: TMutationOptions<organisationType, void>;
}) {
  return useMutation({
    mutationKey: ['approve-organisation', params],
    mutationFn: () => approveOrganisation(params),
    ...options,
  });
}

export function useAddNewOrganisationAdminMutation({
  params,
  options,
}: {
  params: addNewOrganisationAdminParamsType;
  options: TMutationOptions<null, void>;
}) {
  return useMutation({
    mutationKey: ['add-organisation-admin', params],
    mutationFn: () => addNewOrganisationAdmin(params),
    ...options,
  });
}

export function useUpdateOrganisationMutation({
  id,
  params,
  options,
}: {
  id: number;
  params: updateOrganisationParamsType;
  options: TMutationOptions<organisationType, createUpdateOrganisationPayloadType>;
}) {
  return useMutation({
    mutationKey: ['update-organisation', id, params],
    mutationFn: (payload: createUpdateOrganisationPayloadType) => updateOrganisation(id, payload, params),
    ...options,
  });
}

export function useDeleteOrganisationMutation({
  id,
  params,
  options,
}: {
  id: number;
  params: { project_id: number };
  options: TMutationOptions<unknown, number>;
}) {
  return useMutation({
    mutationKey: ['delete-organisation'],
    mutationFn: () => deleteOrganisation(id, params),
    ...options,
  });
}

export function useRemoveOrganisationAdminMutation({
  user_sub,
  params,
  options,
}: {
  user_sub: string;
  params: removeOrganisationAdminParamsType;
  options: TMutationOptions<unknown, number>;
}) {
  return useMutation({
    mutationKey: ['remove-organisation-admin', params],
    mutationFn: () => removeOrganisationAdmin(user_sub, params),
    ...options,
  });
}
