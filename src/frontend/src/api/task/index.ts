import { useQuery, useMutation } from '@tanstack/react-query';
import { addNewTaskEvent, getTaskActivity, getTaskById, getTaskEventHistory, getTasks } from '@/services/task';
import type {
  addNewTaskEventPayloadType,
  addNewTaskEventParamsType,
  taskEventType,
  getTasksParamsType,
  taskType,
  getTaskActivityParamsType,
  taskActivityType,
  getTaskEventHistoryParamsType,
} from './types';
import { TQueryOptions, TMutationOptions } from '@/types';

export function useGetTasksQuery({
  params,
  options,
}: {
  params: getTasksParamsType;
  options: TQueryOptions<taskType[]>;
}) {
  return useQuery({
    queryFn: () => getTasks(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useAddNewTaskEventMutation({
  id,
  options,
}: {
  id: number;
  options: TMutationOptions<
    taskEventType,
    { payload: addNewTaskEventPayloadType; params: addNewTaskEventParamsType },
    { detail: string }
  >;
}) {
  return useMutation({
    mutationFn: ({ payload, params }) => addNewTaskEvent(id, payload, params),
    ...options,
  });
}

export function useGetTaskActivityQuery({
  params,
  options,
}: {
  params: getTaskActivityParamsType;
  options: TQueryOptions<taskActivityType[]>;
}) {
  return useQuery({
    queryFn: () => getTaskActivity(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetTaskByIdQuery({
  id,
  params,
  options,
}: {
  id: number;
  params: getTasksParamsType;
  options: TQueryOptions<taskType>;
}) {
  return useQuery({
    queryFn: () => getTaskById(id, params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetTaskEventHistoryQuery({
  id,
  params,
  options,
}: {
  id: number;
  params: getTaskEventHistoryParamsType;
  options: TQueryOptions<taskEventType[]>;
}) {
  return useQuery({
    queryFn: () => getTaskEventHistory(id, params),
    select: (data) => data.data,
    ...options,
  });
}
