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
import { Tooltip } from '@mui/material';
import Searchbar from '@/components/common/SearchBar';
import useDebouncedInput from '@/hooks/useDebouncedInput';
import isEmpty from '@/utilfunctions/isEmpty';
import Select2 from '@/components/common/Select2';
import { taskStatusList } from '@/constants/taskStatusListConstants';
import type { Polygon as PolygonType } from 'geojson';

type taskListPropType = { map: any; setSelectedTab: (tab: 'task_activity') => void };

type taskListType = {
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
  feature_count: number;
  id: number;
  index: number;
  outline: PolygonType;
  submission_count: number;
  task_state: string;
};

const TaskList = ({ map, setSelectedTab }: taskListPropType) => {
  const params = useParams();
  const dispatch = useDispatch();
  const projectId: string | undefined = params.id;

  const [taskList, setTaskList] = useState<taskListType[]>([]);
  const [filteredTaskList, setFilteredTaskList] = useState<taskListType[]>([]);
  const [filter, setFilters] = useState({ search: '', status: '' });

  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 500,
    init: filter.search,
    onChange: (debouncedEvent) => setFilters((prev) => ({ ...prev, search: debouncedEvent.target.value })),
  });

  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const taskInfoLoading = useAppSelector((state) => state.task.taskLoading);
  const projectDetailsLoading = useAppSelector((state) => state.project.projectDetailsLoading);
  const projectTaskBoundries = useAppSelector((state) => state.project.projectTaskBoundries);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const taskBoundaries = projectTaskBoundries.find((project) => project.id.toString() === projectId)?.taskBoundries;

  useEffect(() => {
    if (taskBoundaries?.length === 0) return;
    const taskFeatureMap = taskBoundaries?.map((task) => {
      const taskFeature = taskInfo?.find((taskInfo) => +taskInfo.index === task.index);
      return {
        ...task,
        feature_count: taskFeature?.feature_count || 0,
        submission_count: taskFeature?.submission_count || 0,
      };
    }) as taskListType[];
    setTaskList(taskFeatureMap);
  }, [projectTaskBoundries, taskInfo]);

  useEffect(() => {
    if (isEmpty(taskList)) return;

    if (filter.search || filter.status) {
      const filteredList = taskList?.filter((task) => {
        const matchesStatus = filter.status ? task?.task_state === filter.status : true;
        const matchesSearch = filter.search ? task?.index?.toString().includes(filter.search.toString()) : true;

        return matchesStatus && matchesSearch;
      });
      setFilteredTaskList(filteredList);
    } else {
      setFilteredTaskList(taskList);
    }
  }, [taskList, filter]);

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
            <Tooltip title="Zoom to task" arrow>
              <AssetModules.MapOutlinedIcon
                className="!fmtm-text-sm fmtm-text-grey-800 hover:fmtm-text-grey-900 fmtm-cursor-pointer"
                onClick={() => zoomToTask(row?.original?.index)}
              />
            </Tooltip>
            <Tooltip title="Task history" arrow>
              <AssetModules.HistoryOutlinedIcon
                className="!fmtm-text-sm fmtm-text-grey-800 hover:fmtm-text-grey-900 fmtm-cursor-pointer"
                onClick={() => showTaskHistory(row?.original?.index)}
              />
            </Tooltip>
          </div>
        );
      },
    },
  ];

  return (
    <div className="fmtm-h-[calc(100%-47px)]">
      <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mb-2">
        <Searchbar
          value={searchTextData}
          onChange={handleChangeData}
          type="number"
          placeholder="Search by ID"
          wrapperStyle="!fmtm-w-[10rem] fmtm-rounded"
        />
        <Select2
          options={taskStatusList || []}
          value={filter.status}
          onChange={(value: any) => {
            setFilters({ ...filter, status: value });
          }}
          placeholder="All Status"
          className="!fmtm-w-[12rem] fmtm-bg-white fmtm-rounded"
        />
      </div>
      <DataTable
        data={filteredTaskList || []}
        columns={taskDataColumns}
        isLoading={taskInfoLoading || projectDetailsLoading}
        tableWrapperClassName="fmtm-flex-1 fmtm-h-[calc(100%-4rem)]"
      />
    </div>
  );
};

export default TaskList;
