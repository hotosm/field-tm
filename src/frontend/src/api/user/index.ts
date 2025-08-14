import { useQuery } from '@tanstack/react-query';
import { getUserList } from '@/services/user';
import type { TQueryOptions } from '@/types';
import type { getUserListParamsType, getUserListType } from './types';

export function useGetUserListQuery({
  params,
  options,
}: {
  params: getUserListParamsType;
  options: TQueryOptions<getUserListType[]>;
}) {
  return useQuery({
    queryFn: () => getUserList(params),
    select: (data) => data.data,
    ...options,
  });
}
