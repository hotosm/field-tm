import React, { useState, useEffect } from 'react';
import environment from '../environment';
import ProjectTaskStatus from '../api/ProjectTaskStatus';
import MapStyles from '../hooks/MapStyles';
import CoreModules from '../shared/CoreModules';
import { CommonActions } from '../store/slices/CommonSlice';
export default function Dialog({ taskId, feature, map, view }) {
  // const featureStatus = feature.id_ != undefined ? feature.id_.replace("_", ",").split(',')[1] : null;
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const loading = CoreModules.useAppSelector((state) => state.common.loading);
  const [list_of_task_status, set_list_of_task_status] = useState([]);
  const [task_status, set_task_status] = useState('READY');

  const geojsonStyles = MapStyles();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const currentProjectId = environment.decode(params.id);
  const currentTaskId = environment.encode(taskId);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return task.id == taskId;
    })?.[0],
  };

  useEffect(() => {
    if (projectIndex != -1) {
      const currentStatus = {
        ...projectData[projectIndex].taskBoundries.filter((task) => {
          return task.id == taskId;
        })[0],
      };
      const findCorrectTaskStatusIndex = environment.tasksStatus.findIndex(
        (data) => data.label == currentStatus.task_status,
      );
      const tasksStatus =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['label'] : '';
      set_task_status(tasksStatus);
      const tasksStatusList =
        feature.id_ != undefined ? environment.tasksStatus[findCorrectTaskStatusIndex]?.['action'] : [];

      set_list_of_task_status(tasksStatusList);
    }
  }, [projectData, taskId, feature]);

  // const tasksList = environment.tasksStatus.map((status) => {
  //   return status.key;
  // });

  const handleOnClick = (event) => {
    const status = event.target.id;
    const body = token != null ? { ...token } : {};
    const geoStyle = geojsonStyles[status];
    if (event.target.id != undefined) {
      if (body.hasOwnProperty('id')) {
        dispatch(
          ProjectTaskStatus(
            `${import.meta.env.VITE_API_URL}/tasks/${taskId}/new_status/${status}`,
            geoStyle,
            projectData,
            currentProjectId,
            feature,
            map,
            view,
            taskId,
            body,
          ),
        );
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Something is wrong with the user.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    } else {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Oops!, Please try again.',
          variant: 'error',
          duration: 2000,
        }),
      );
    }
  };
  const checkIfTaskAssignedOrNot =
    currentStatus?.locked_by_username === token?.username || currentStatus?.locked_by_username === null;

  return (
    <CoreModules.Stack direction={'column'} spacing={2}>
      <CoreModules.Stack direction={'row'} pl={1}>
        <CoreModules.Typography fontWeight={'bold'} variant="h3">
          {`Task : ${taskId}`}
        </CoreModules.Typography>
      </CoreModules.Stack>
      <CoreModules.Stack direction={'row'} pl={1}>
        <CoreModules.Typography variant="h3">
          {`STATUS : ${task_status?.toString()?.replaceAll('_', ' ')}`}
        </CoreModules.Typography>
      </CoreModules.Stack>
      <CoreModules.Link
        to={`/project/${params.id}/tasks/${currentTaskId}`}
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          textDecoration: 'none',
          marginRight: '15px',
        }}
      >
        <CoreModules.Button
          // id={data.value}
          // key={index}
          variant="contained"
          color="error"
          // onClick={handleOnClick}
          // disabled={loading}
        >
          Task Submission
        </CoreModules.Button>
      </CoreModules.Link>
      {checkIfTaskAssignedOrNot &&
        list_of_task_status?.map((data, index) => {
          return list_of_task_status?.length != 0 ? (
            <CoreModules.Button
              id={data.value}
              key={index}
              variant="contained"
              color="error"
              onClick={handleOnClick}
              disabled={loading}
            >
              {data.key}
            </CoreModules.Button>
          ) : (
            <CoreModules.Button
              id={data.value}
              key={index}
              variant="contained"
              color="error"
              onClick={handleOnClick}
              disabled={true}
            >
              {data.key}
            </CoreModules.Button>
          );
        })}
    </CoreModules.Stack>
  );
}
