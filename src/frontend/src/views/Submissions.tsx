// TODO should this be deleted??

import React, { useEffect } from 'react';
// import '../styles/home.css'
import CoreModules from '@/shared/CoreModules';
// import { useLocation, useNavigate } from 'react-router-dom';
import Avatar from '@/assets/images/avatar.png';
// import SubmissionMap from '@/components/SubmissionMap/SubmissionMap';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { ProjectById } from '@/api/Project';

const Submissions = () => {
  const dispatch = CoreModules.useAppDispatch();
  const state = CoreModules.useAppSelector((state) => state.project);
  const projectInfo = CoreModules.useAppSelector((state) => state.home.selectedProject);
  const projectSubmissionState = CoreModules.useAppSelector((state) => state.project.projectSubmission);
  const projectState = CoreModules.useAppSelector((state) => state.project.project);
  // const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  // const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const params = CoreModules.useParams();
  const projectId = params.id;
  // const theme = CoreModules.useAppSelector(state => state.theme.hotTheme)
  useEffect(() => {
    dispatch(ProjectSubmissionService(`${import.meta.env.VITE_API_URL}/submission/?project_id=${projectId}`));
    // dispatch(ProjectDataExtractService(`${import.meta.env.VITE_API_URL}/projects/${projectId}/features`));
    //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
  }, []);

  // Requesting Task Boundaries on Page Load
  useEffect(() => {
    if (state.projectTaskBoundries.findIndex((project) => project.id == projectId) == -1) {
      dispatch(ProjectById(projectId));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != projectId) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);
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
            <CoreModules.Button variant="contained" color="error">
              Monitoring
            </CoreModules.Button>

            {/* END */}

            {/* Upload Area SideBar Button for uploading Area page  */}
            <CoreModules.Button variant="contained" color="error">
              Convert
            </CoreModules.Button>
            <a href={`${import.meta.env.VITE_API_URL}/submission/download?project_id=${projectId}`} download>
              <CoreModules.Button variant="contained" color="error">
                Download CSV
              </CoreModules.Button>
            </a>
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
              overflowY: 'scroll',
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
                <CoreModules.Box
                  key={submission.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    background: 'white',
                    borderRadius: '10px',
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
              );
            })}
          </CoreModules.Box>
        </CoreModules.Stack>
        <CoreModules.Box sx={{ width: '100%', ml: 6, border: '1px solid green' }}>
          {/* <SubmissionMap /> */}
        </CoreModules.Box>
      </CoreModules.Stack>
    </CoreModules.Box>
  );
};

export default Submissions;
