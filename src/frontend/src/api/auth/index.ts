import { useQuery } from '@tanstack/react-query';
import type { TQueryOptions, getOsmCallbackParams, getOsmLoginUrlResponse } from '@/types';
import { getOsmLoginUrl, osmCallback } from '@/services/auth';

export function useGetOsmLoginUrlQuery({ options }: { options: TQueryOptions<getOsmLoginUrlResponse> }) {
  return useQuery({
    queryFn: () => getOsmLoginUrl(),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetOsmCallbackQuery({
  params,
  options,
}: {
  params: getOsmCallbackParams;
  options: TQueryOptions<void>;
}) {
  return useQuery({
    queryFn: () => osmCallback(params),
    select: (data) => data.data,
    ...options,
  });
}
