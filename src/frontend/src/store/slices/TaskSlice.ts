import { createSlice } from '@reduxjs/toolkit';
import { TaskStateTypes } from '@/store/types/ITask';
import { taskSubmissionInfoType } from '@/models/task/taskModel';
import { EntityOsmMap } from '@/store/types/IProject';

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
  projectBoundary: [],
  convertToOsmLoading: false,
  convertToOsm: [],
  downloadSubmissionLoading: { type: '', loading: false },
  convertXMLToJOSMLoading: false,
  josmEditorError: null,
};

const TaskSlice = createSlice({
  name: 'task',
  initialState: initialState,
  reducers: {
    GetProjectBoundaryLoading(state, action) {
      state.projectBoundaryLoading = action.payload;
    },

    FetchConvertToOsmLoading(state, action) {
      state.convertToOsmLoading = action.payload;
    },

    SetTaskSubmissionStatesLoading(state, action) {
      state.taskLoading = action.payload;
    },

    SetTaskSubmissionStates(state, action) {
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
            submissionCount++;
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

    SetSelectedTask(state, action) {
      state.selectedTask = action.payload;
    },

    SetSelectedFeatureProps(state, action) {
      state.selectedFeatureProps = action.payload;
    },

    GetDownloadProjectBoundary(state, action) {
      state.projectBoundary = action.payload;
    },
    FetchConvertToOsm(state, action) {
      state.convertToOsm = action.payload;
    },
    GetDownloadProjectSubmissionLoading(state, action) {
      state.downloadSubmissionLoading = action.payload;
    },
    SetConvertXMLToJOSMLoading(state, action) {
      state.convertXMLToJOSMLoading = action.payload;
    },
    SetJosmEditorError(state, action) {
      state.josmEditorError = action.payload;
    },
  },
});

export const TaskActions = TaskSlice.actions;
export default TaskSlice;
