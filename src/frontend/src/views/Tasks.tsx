import React, { useEffect, useState } from 'react';
// import '../styles/home.css'
import '../../node_modules/ol/ol.css';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
// import { useLocation, useNavigate } from 'react-router-dom';
// import { styled, alpha } from '@mui/material';

import Avatar from '../assets/images/avatar.png';
import SubmissionMap from '../components/SubmissionMap/SubmissionMap';
import environment from '../environment';
import { ProjectBuildingGeojsonService, ProjectSubmissionService } from '../api/SubmissionService';
import { ProjectActions } from '../store/slices/ProjectSlice';
import { ProjectById } from '../api/Project';
import { getDownloadProjectSubmission } from '../api/task';
const basicGeojsonTemplate = {
  type: 'FeatureCollection',
  features: [],
};

const TasksSubmission = () => {
  const dispatch = CoreModules.useAppDispatch();
  const state = CoreModules.useAppSelector((state) => state.project);
  const projectInfo = CoreModules.useAppSelector((state) => state.home.selectedProject);
  const projectSubmissionState = CoreModules.useAppSelector((state) => state.project.projectSubmission);
  const projectState = CoreModules.useAppSelector((state) => state.project.project);
  // const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  // const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const params = CoreModules.useParams();
  const encodedProjectId = params.projectId;
  const decodedProjectId = environment.decode(encodedProjectId);
  const encodedTaskId = params.taskId;
  const decodedTaskId = environment.decode(encodedTaskId);
  // const theme = CoreModules.useAppSelector(state => state.theme.hotTheme)
  useEffect(() => {
    dispatch(
      ProjectSubmissionService(
        `${environment.baseApiUrl}/submission/?project_id=${decodedProjectId}&task_id=${decodedTaskId}`,
      ),
    );
    dispatch(
      ProjectBuildingGeojsonService(
        `${environment.baseApiUrl}/projects/${decodedProjectId}/features?task_id=${decodedTaskId}`,
      ),
    );
    //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
  }, []);
  //Fetch project for the first time
  useEffect(() => {
    if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(encodedProjectId)) == -1) {
      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedProjectId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedProjectId),
        ),
        state.projectTaskBoundries,
      );
      dispatch(
        ProjectBuildingGeojsonService(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedProjectId)}/features`,
        ),
      );
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedProjectId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedProjectId),
        ),
        state.projectTaskBoundries,
      );
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedProjectId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);
  const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const [projectBoundaries, setProjectBoundaries] = useState(null);
  const [buildingBoundaries, setBuildingBoundaries] = useState(null);

  if (projectTaskBoundries?.length > 0 && projectBoundaries === null) {
    const taskGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectTaskBoundries?.[0]?.taskBoundries
          ?.filter((task) => task.id === decodedTaskId)
          .map((task) => ({
            ...task.outline_geojson,
            id: task.outline_geojson.properties.uid,
          })),
      ],
    };
    console.log(taskGeojsonFeatureCollection, 'taskGeojsonFeatureCollection');
    setProjectBoundaries(taskGeojsonFeatureCollection);
  }
  if (projectBuildingGeojson?.length > 0 && buildingBoundaries === null) {
    const buildingGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectBuildingGeojson
          ?.filter((task) => task.task_id === decodedTaskId)
          .map((task) => ({ ...task.geometry, id: task.id })),
      ],
      // features: projectBuildingGeojson.map((feature) => ({ ...feature.geometry, id: feature.id }))
    };
    setBuildingBoundaries(buildingGeojsonFeatureCollection);
  }

  const StyledMenu = AssetModules.styled((props) => (
    <CoreModules.Menu
      elevation={0}
      anchorOrigin={
        {
          // vertical: 'bottom',
          // horizontal: 'right',
        }
      }
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      {...props}
    />
  ))(({ theme }) => ({
    '& .MuiPaper-root': {
      borderRadius: 6,
      marginTop: theme.spacing(1),
      minWidth: 180,
      color: theme.palette.mode === 'light' ? 'rgb(55, 65, 81)' : theme.palette.grey[300],
      boxShadow:
        'rgb(255, 255, 255) 0px 0px 0px 0px, rgba(0, 0, 0, 0.05) 0px 0px 0px 1px, rgba(0, 0, 0, 0.1) 0px 10px 15px -3px, rgba(0, 0, 0, 0.05) 0px 4px 6px -2px',
      '& .MuiMenu-list': {
        padding: '4px 0',
      },
      '& .MuiMenuItem-root': {
        '& .MuiSvgIcon-root': {
          fontSize: 18,
          color: theme.palette.text.secondary,
          marginRight: theme.spacing(1.5),
        },
        '&:active': {
          backgroundColor: AssetModules.alpha(theme.palette.primary.main, theme.palette.action.selectedOpacity),
        },
      },
    },
  }));

  const handleDownload = (downloadType) => {
    if (downloadType === 'csv') {
      dispatch(
        getDownloadProjectSubmission(
          `${environment.baseApiUrl}/submission/download?project_id=${decodedProjectId}&task_id=${decodedTaskId}&export_json=false`,
        ),
      );
    } else if (downloadType === 'json') {
      dispatch(
        getDownloadProjectSubmission(
          `${environment.baseApiUrl}/submission/download?project_id=${decodedProjectId}&task_id=${decodedTaskId}&export_json=true`,
        ),
      );
    }
  };

  const downloadSubmissionLoading = CoreModules.useAppSelector((state) => state.task.downloadSubmissionLoading);

  return (
    <CoreModules.Box sx={{ px: 25, py: 6 }}>
      <CoreModules.Stack
        sx={{
          display: 'flex',
          flexDirection: 'row',
          height: 'calc(100vh - 190px)',
        }}
      >
        <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '51%' }}>
          <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', gap: 1 }}>
            {/* Project Details SideBar Button for Creating Project */}
            <CoreModules.Button sx={{ width: 'unset' }} variant="contained" color="error">
              Monitoring
            </CoreModules.Button>

            {/* END */}

            {/* Upload Area SideBar Button for uploading Area page  */}
            <CoreModules.Button sx={{ width: 'unset' }} variant="contained" color="error">
              Convert
            </CoreModules.Button>
            <CoreModules.LoadingButton
              onClick={() => handleDownload('csv')}
              sx={{ width: 'unset' }}
              loading={downloadSubmissionLoading.type === 'csv' && downloadSubmissionLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              CSV
            </CoreModules.LoadingButton>

            <CoreModules.LoadingButton
              onClick={() => handleDownload('json')}
              sx={{ width: 'unset' }}
              loading={downloadSubmissionLoading.type === 'json' && downloadSubmissionLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              JSON
            </CoreModules.LoadingButton>

            {/* END */}
          </CoreModules.Stack>
          <CoreModules.Box
            component="h4"
            sx={{
              background: '#e1e1e1',
              mt: 5,
              height: '90%',
              p: 5,
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              borderRadius: '10px',
            }}
          >
            {projectSubmissionState?.map((submission) => {
              const date = new Date(submission.createdAt);

              const dateOptions = {
                minute: 'numeric',
                hour: 'numeric',
                day: 'numeric',
                weekday: 'long',
                year: 'numeric',
                month: 'long',
              };

              const formattedDate = date.toLocaleDateString('en-US', dateOptions);
              return (
                <CoreModules.Link
                  style={{ textDecoration: 'auto' }}
                  className="submission-item"
                  to={`/project/${encodedProjectId}/tasks/${encodedTaskId}/submission/${submission.instanceId}`}
                >
                  <CoreModules.Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      background: 'white',
                      borderRadius: '10px',
                      p: '0.5rem',
                    }}
                  >
                    <CoreModules.Box>
                      <img src={Avatar} style={{ marginRight: '10px', marginLeft: '5px' }} />{' '}
                    </CoreModules.Box>
                    <CoreModules.Box>
                      <CoreModules.Typography variant="subtitle1" noWrap mt={'2%'} ml={'3%'}>
                        {submission.submitted_by}
                      </CoreModules.Typography>
                      <CoreModules.Typography variant="subtitle3" sx={{ color: 'gray' }} mt={'2%'} ml={'3%'}>
                        Submitted {projectState?.project} at {formattedDate}
                      </CoreModules.Typography>
                    </CoreModules.Box>
                  </CoreModules.Box>
                </CoreModules.Link>
              );
            })}
          </CoreModules.Box>
        </CoreModules.Stack>
        <CoreModules.Box sx={{ width: '100%', ml: 6, border: '1px solid green' }}>
          <SubmissionMap outlineBoundary={projectBoundaries} featureGeojson={buildingBoundaries} />
        </CoreModules.Box>
      </CoreModules.Stack>
    </CoreModules.Box>
  );
};

export default TasksSubmission;
