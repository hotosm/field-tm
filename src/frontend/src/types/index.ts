import type { AxiosResponse } from 'axios';
import type { UseQueryOptions, QueryKey, UseMutationOptions } from '@tanstack/react-query';

export * from '@/api/auth/types';
export * from '@/api/central/types';
export * from '@/api/helper/types';
export * from '@/api/organisation/types';
export * from '@/api/project/types';
export * from '@/api/submission/types';
export * from '@/api/task/types';
export * from '@/api/user/types';

// Generic type for UseQueryOptions
export type TQueryOptions<TData, TError = Error, TQueryKey extends QueryKey = QueryKey> = UseQueryOptions<
  AxiosResponse<TData>,
  TError,
  TData,
  TQueryKey
>;

// Generic type for UseMutationOptions
export type TMutationOptions<TData, TVariables, TError = Error> = UseMutationOptions<
  AxiosResponse<TData>,
  TError,
  TVariables
>;
