/* eslint-disable react/jsx-key */
import React, { useEffect, useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import { Feature } from 'ol';
import { Polygon } from 'ol/geom';
import { useAppSelector } from '@/types/reduxTypes';
import { projectTaskActivity } from '@/store/types/IProject';
import { projectTaskBoundriesType } from '@/models/project/projectModel';
import { task_event, task_state_labels } from '@/types/enums';
import ActivitiesCardSkeleton from '@/components/Skeletons/ProjectDetails/ActivitiesCardSkeleton';
import ShowingCountSkeleton from '@/components/Skeletons/ProjectDetails/ShowingCountSkeleton';

type taskActivityType = {
  defaultTheme: any;
  state: projectTaskBoundriesType[];
  params: Record<string, any>;
  map: any;
};

const TaskActivity = ({ defaultTheme, state, params, map }: taskActivityType) => {
  const [searchText, setSearchText] = useState<string>('');
  const [taskHistories, setTaskHistories] = useState<projectTaskActivity[]>([]);
  const [allActivities, setAllActivities] = useState(0);
  const projectActivityLoading = useAppSelector((state) => state?.project?.projectActivityLoading);
  const projectTaskActivityList = useAppSelector((state) => state?.project?.projectTaskActivity);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const projectTaskIdIndexMap = useAppSelector((state) => state?.project?.projectTaskIdIndexMap);

  const handleOnchange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(event.target.value);
  };

  useEffect(() => {
    let taskHistories: projectTaskActivity[] = projectTaskActivityList;

    setAllActivities(projectTaskActivityList.length);
    let finalTaskEvents: projectTaskActivity[] = taskHistories.filter((task) => {
      return task?.username?.replace(/\s+/g, '')?.toString().includes(searchText.toString());
    });
    if (searchText != '') {
      setTaskHistories(finalTaskEvents);
    } else {
      setTaskHistories(taskHistories);
    }
  }, [state, searchText, projectTaskActivityList, selectedTask]);

  const zoomToTask = (taskId: number | null) => {
    let geojson: Record<string, any> = {};
    const index = state.findIndex((project) => project.id == params.id);
    if (index != -1) {
      const taskIndex = state[index]?.taskBoundries.findIndex((task) => task?.id == taskId);
      if (index != -1) {
        geojson = state[index]?.taskBoundries[taskIndex]?.outline;
      }
    }

    const olFeature = new Feature({
      geometry: new Polygon(geojson?.coordinates).transform('EPSG:4326', 'EPSG:3857'),
    });
    // Get the extent of the OpenLayers feature
    const extent = olFeature.getGeometry()?.getExtent();
    map.getView().fit(extent, {
      padding: [0, 0, 0, 0],
    });
  };

  const ActivitiesCard = ({ taskEvent }: { taskEvent: projectTaskActivity }) => {
    const actionDate = taskEvent?.created_at?.split('T')[0];
    const actionTime = `${taskEvent?.created_at?.split('T')[1].split(':')[0]}:${
      taskEvent?.created_at?.split('T')[1].split(':')[1]
    }`;
    return (
      <div className="fmtm-flex fmtm-gap-2 fmtm-items-center fmtm-justify-between fmtm-px-1 fmtm-border-b-[2px] fmtm-border-white fmtm-py-3">
        <div className="fmtm-flex fmtm-items-center fmtm-flex-1">
          <div className="fmtm-w-[2.81rem] fmtm-h-[2.81rem] fmtm-border fmtm-rounded-full fmtm-overflow-hidden fmtm-mr-4">
            {taskEvent?.profile_img ? (
              <img src={taskEvent?.profile_img} alt="Profile Picture" />
            ) : (
              <div className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-bg-white">
                <AssetModules.PersonIcon color="success" sx={{ fontSize: '30px' }} />
              </div>
            )}
          </div>
          <div className="fmtm-text-base fmtm-flex-1">
            {taskEvent.event === task_event.ASSIGN ? (
              <>
                <span style={{ color: defaultTheme.statusTextTheme[taskEvent?.state] }}>
                  Task
                  <span className="fmtm-text-[#7A7676] fmtm-font-extralight fmtm-italic "> assigned to </span>
                </span>{' '}
                <span className="fmtm-text-[#555555] fmtm-font-medium">{taskEvent?.username}</span>
              </>
            ) : (
              <>
                <span className="fmtm-text-[#555555] fmtm-font-medium">{taskEvent?.username} </span>
                <span className="fmtm-text-[#7A7676] fmtm-font-extralight fmtm-italic ">updated status to </span>
                <span style={{ color: defaultTheme.statusTextTheme[taskEvent?.state] }}>
                  {task_state_labels[taskEvent?.state]}
                </span>
              </>
            )}
            <div className="fmtm-flex fmtm-items-center fmtm-justify-between">
              <p className="fmtm-text-sm fmtm-text-[#7A7676]">
                #{selectedTask ? projectTaskIdIndexMap?.[selectedTask] : selectedTask}
              </p>
              <div className="fmtm-flex fmtm-items-center fmtm-gap-1">
                <AssetModules.AccessTimeIcon className="fmtm-text-primaryRed" style={{ fontSize: '20px' }} />
                <p className="fmtm-text-sm fmtm-text-[#7A7676]">
                  <span>{actionDate} </span>
                  <span>{actionTime}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
        <div title="Zoom to Task" onClick={() => zoomToTask(selectedTask)}>
          <AssetModules.MapIcon
            className="fmtm-text-[#9B9999] hover:fmtm-text-[#555555] fmtm-cursor-pointer"
            style={{ fontSize: '20px' }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="fmtm-w-full fmtm-px-2 sm:fmtm-px-0 fmtm-relative sm:fmtm-overflow-y-scroll scrollbar">
      <div className="fmtm-sticky fmtm-overflow-y-scroll scrollbar sm:fmtm-overflow-visible -fmtm-top-[2px] sm:fmtm-top-0 fmtm-bg-white md:fmtm-bg-grey-100">
        <div className="fmtm-flex fmtm-items-center fmtm-w-full fmtm-justify-between fmtm-gap-4">
          <input
            type="text"
            onChange={handleOnchange}
            value={searchText}
            placeholder="Search by username"
            className="fmtm-w-full fmtm-text-md fmtm-px-2 fmtm-py-[0.18rem] fmtm-outline-none fmtm-border-[1px] fmtm-border-[#E7E2E2] fmtm-mr-2"
          />
        </div>
        {projectActivityLoading ? (
          <ShowingCountSkeleton />
        ) : (
          <p className="fmtm-text-[#A8A6A6] fmtm-text-base fmtm-my-1">
            showing {taskHistories?.length} of {allActivities} activities
          </p>
        )}
      </div>
      <div>
        {projectActivityLoading ? (
          <div>
            {Array.from({ length: 10 }).map((_, i) => (
              <ActivitiesCardSkeleton key={i} />
            ))}
          </div>
        ) : taskHistories?.length === 0 ? (
          <p className="fmtm-mt-5 fmtm-text-center fmtm-text-xl fmtm-text-gray-400">No Task History!</p>
        ) : (
          <div>{taskHistories?.map((taskEvent) => <ActivitiesCard taskEvent={taskEvent} />)}</div>
        )}
      </div>
    </div>
  );
};

export default TaskActivity;
