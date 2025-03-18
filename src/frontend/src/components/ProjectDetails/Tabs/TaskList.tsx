import React, { useEffect, useState } from 'react';
import { Feature } from 'ol';
import { Polygon } from 'ol/geom';
import { useParams } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import { task_state_labels } from '@/types/enums';
import AssetModules from '@/shared/AssetModules';
import DataTable from '@/components/common/DataTable';
import { useDispatch } from 'react-redux';
import { TaskActions } from '@/store/slices/TaskSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';

type taskListPropType = { map: any; setSelectedTab: (tab: 'task_activity') => void };

type taskListType = {
  task_state: string | undefined;
  task_id: string;
  index: string;
  submission_count: number;
  last_submission: string | null;
  feature_count: number;
};

const TaskList = ({ map, setSelectedTab }: taskListPropType) => {
  const params = useParams();
  const dispatch = useDispatch();
  const projectId: string | undefined = params.id;

  const [taskList, setTaskList] = useState<taskListType[]>([]);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const taskInfoLoading = useAppSelector((state) => state.task.taskLoading);
  const projectDetailsLoading = useAppSelector((state) => state.project.projectDetailsLoading);
  const projectTaskBoundries = useAppSelector((state) => state.project.projectTaskBoundries);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const taskBoundaries = projectTaskBoundries.find((project) => project.id.toString() === projectId)?.taskBoundries;

  useEffect(() => {
    if (taskInfo?.length === 0 || taskBoundaries?.length === 0) return;
    const updatedTaskList = taskInfo?.map((task) => ({
      ...task,
      task_state: taskBoundaries?.find((taskBound) => taskBound?.index === +task?.index)?.task_state,
    }));
    setTaskList(updatedTaskList);
  }, [projectTaskBoundries, taskInfo]);

  const zoomToTask = (taskIndex: string) => {
    let geojson: Record<string, any> | undefined = taskBoundaries?.find((task) => task.index === +taskIndex)?.outline;
    if (!geojson) return;
    const olFeature = new Feature({
      geometry: new Polygon(geojson?.coordinates).transform('EPSG:4326', 'EPSG:3857'),
    });
    const extent = olFeature.getGeometry()?.getExtent();
    map.getView().fit(extent, {
      padding: [0, 0, 0, 0],
    });
  };

  const showTaskHistory = (taskIndex: string) => {
    dispatch(TaskActions.SetSelectedTask(+taskIndex));
    dispatch(ProjectActions.ToggleTaskModalStatus(true));
    setSelectedTab('task_activity');
    zoomToTask(taskIndex);
  };

  const taskDataColumns = [
    {
      header: 'ID',
      cell: ({ row }: any) => {
        return <p className="fmtm-text-grey-800 fmtm-body-md">{row?.original?.index}</p>;
      },
    },
    {
      header: 'Submission Count',
      cell: ({ row }: any) => {
        return (
          <p className="fmtm-body-md">
            <span className="fmtm-text-primaryRed">{row?.original?.submission_count}/</span>
            <span className="fmtm-text-grey-800">{row?.original?.feature_count}</span>
          </p>
        );
      },
    },
    {
      header: 'Status',
      cell: ({ row }: any) => {
        return (
          <p
            style={{ backgroundColor: defaultTheme.palette.mapFeatureColors[row?.original?.task_state] }}
            className="fmtm-bg-opacity-50 fmtm-w-fit fmtm-py-1 fmtm-px-2 fmtm-rounded-2xl fmtm-border fmtm-border-grey-200 fmtm-text-xs fmtm-text-grey-800"
          >
            {task_state_labels[row?.original?.task_state]}
          </p>
        );
      },
    },
    {
      header: ' ',
      cell: ({ row }: any) => {
        return (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-4 fmtm-px-4">
            <AssetModules.MapOutlinedIcon
              className="!fmtm-text-sm fmtm-text-grey-800 hover:fmtm-text-grey-900 fmtm-cursor-pointer"
              onClick={() => zoomToTask(row?.original?.index)}
            />
            <AssetModules.HistoryOutlinedIcon
              className="!fmtm-text-sm fmtm-text-grey-800 hover:fmtm-text-grey-900 fmtm-cursor-pointer"
              onClick={() => showTaskHistory(row?.original?.index)}
            />
          </div>
        );
      },
    },
  ];

  return (
    <div className="fmtm-h-[calc(100%-47px)]">
      <DataTable
        data={taskList || []}
        columns={taskDataColumns}
        isLoading={taskInfoLoading || projectDetailsLoading}
        tableWrapperClassName="fmtm-flex-1 fmtm-h-full"
      />
    </div>
  );
};

export default TaskList;
