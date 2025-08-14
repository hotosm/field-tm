import { useMutation } from '@tanstack/react-query';
import { addNewTaskEvent } from '@/services/task';
import type { addNewTaskEventPayloadType, addNewTaskEventParamsType, addNewTaskEventResponseType } from './types';
import { TMutationOptions } from '@/types';

export function useAddNewTaskEventMutation({
  id,
  params,
  options,
}: {
  id: number;
  params: addNewTaskEventParamsType;
  options: TMutationOptions<addNewTaskEventResponseType, addNewTaskEventPayloadType>;
}) {
  return useMutation({
    mutationKey: ['add-new-task-event', id, params],
    mutationFn: (payload: addNewTaskEventPayloadType) => addNewTaskEvent(id, payload, params),
    ...options,
  });
}
