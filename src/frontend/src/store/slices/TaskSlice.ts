import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { TaskFeatureSelectionProperties, TaskStateTypes } from '@/store/types/ITask';
import { EntityOsmMap, taskSubmissionInfoType } from '@/models/task/taskModel';

const initialState: TaskStateTypes = {
  taskLoading: false,
  taskInfo: [],
  selectedTask: null,
  selectedFeatureProps: {
    osm_id: 0,
    tags: '',
    timestamp: '',
    version: 0,
    changeset: 0,
  },
  projectBoundaryLoading: false,
  convertToOsmLoading: false,
  downloadSubmissionLoading: { fileType: '', loading: false },
  convertXMLToJOSMLoading: false,
  josmEditorError: null,
};

const TaskSlice = createSlice({
  name: 'task',
  initialState: initialState,
  reducers: {
    SetTaskSubmissionStatesLoading(state, action: PayloadAction<boolean>) {
      state.taskLoading = action.payload;
    },

    SetTaskSubmissionStates(state, action: PayloadAction<EntityOsmMap[]>) {
      const groupedPayload: Record<string, EntityOsmMap[]> = action.payload?.reduce((acc, item) => {
        if (!acc[item.task_id]) {
          acc[item.task_id] = [];
        }
        acc[item.task_id].push(item);
        return acc;
      }, {});

      const taskInfo: taskSubmissionInfoType[] = Object.entries(groupedPayload).map(([taskId, items]) => {
        // Calculate feature_count
        const featureCount = items.length;

        // Calculate submission_count and last_submission
        let submissionCount = 0;
        let lastSubmission: string | null = null;
        items.forEach((item) => {
          if (item.status > 1) {
            const entitySubmissionCount = item?.submission_ids?.split(',')?.length || 0;
            submissionCount += entitySubmissionCount;
          }
          if (item.updated_at && (!lastSubmission || item.updated_at > lastSubmission)) {
            lastSubmission = item.updated_at;
          }
        });

        return {
          task_id: taskId,
          index: taskId,
          submission_count: submissionCount,
          last_submission: lastSubmission,
          feature_count: featureCount,
        };
      });

      state.taskInfo = taskInfo;
    },

    SetSelectedTask(state, action: PayloadAction<number | null>) {
      state.selectedTask = action.payload;
    },

    SetSelectedFeatureProps(state, action: PayloadAction<TaskFeatureSelectionProperties>) {
      state.selectedFeatureProps = action.payload;
    },
    DownloadProjectSubmissionLoading(
      state,
      action: PayloadAction<{ fileType: 'json' | 'csv' | 'geojson'; loading: boolean }>,
    ) {
      state.downloadSubmissionLoading = action.payload;
    },
    SetConvertXMLToJOSMLoading(state, action: PayloadAction<boolean>) {
      state.convertXMLToJOSMLoading = action.payload;
    },
    SetJosmEditorError(state, action: PayloadAction<string | null>) {
      state.josmEditorError = action.payload;
    },
  },
});

export const TaskActions = TaskSlice.actions;
export default TaskSlice;
