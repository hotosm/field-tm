import { TMutationOptions } from '@/types';
import { useMutation } from '@tanstack/react-query';
import { qfieldCredsParamsType } from './types';
import { testQFieldCredentials } from '@/services/qfield';

export function useTestQFieldCredentialsMutation(
  options: TMutationOptions<void, { params: qfieldCredsParamsType }, { detail: string }>,
) {
  return useMutation({
    mutationFn: ({ params }) => testQFieldCredentials(params),
    ...options,
  });
}
