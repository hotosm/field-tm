import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import ProjectInfoSidebar from '../components/ProjectInfo/ProjectInfoSidebar';
import ProjectInfomap from '../components/ProjectInfo/ProjectInfomap';
import environment from '../environment';
import { ProjectActions } from '../store/slices/ProjectSlice';

import { ConvertXMLToJOSM, fetchConvertToOsmDetails, fetchInfoTask, getDownloadProjectSubmission } from '../api/task';
import AssetModules from '../shared/AssetModules';
import { ProjectById } from '../api/Project';
import ProjectInfoCountCard from '../components/ProjectInfo/ProjectInfoCountCard';

const boxStyles = {
  animation: 'blink 1s infinite',
  '@keyframes blink': {
    '0%': {
      opacity: 1,
    },
    '50%': {
      opacity: 0,
    },
    '100%': {
      opacity: 1,
    },
  },
};

const ProjectInfo = () => {
  const dispatch = CoreModules.useAppDispatch();
  const navigate = CoreModules.useNavigate();
  const [isMonitoring, setIsMonitoring] = useState(false);
  const themes = CoreModules.useAppSelector((state) => state.theme.hotTheme);

  const taskInfo = CoreModules.useAppSelector((state) => state.task.taskInfo);
  const selectedTask = CoreModules.useAppSelector((state) => state.task.selectedTask);
  const state = CoreModules.useAppSelector((state) => state.project);

  const params = CoreModules.useParams();
  const encodedId = params.projectId;
  const decodedId = environment.decode(encodedId);

  const handleDownload = (downloadType) => {
    if (downloadType === 'csv') {
      dispatch(
        getDownloadProjectSubmission(
          `${environment.baseApiUrl}/submission/download?project_id=${decodedId}&export_json=false`,
        ),
      );
    } else if (downloadType === 'json') {
      dispatch(
        getDownloadProjectSubmission(
          `${environment.baseApiUrl}/submission/download?project_id=${decodedId}&export_json=true`,
        ),
      );
    }
  };
  //Fetch project for the first time
  useEffect(() => {
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(encodedId)) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));

      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedId),
        ),
        state.projectTaskBoundries,
      );
      // dispatch(ProjectBuildingGeojsonService(`${environment.baseApiUrl}/projects/${environment.decode(encodedId)}/features`))
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedId),
        ),
        state.projectTaskBoundries,
      );
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);
  const handleConvert = () => {
    dispatch(
      fetchConvertToOsmDetails(
        `${environment.baseApiUrl}/submission/convert-to-osm?project_id=${decodedId}&${
          selectedTask ? `task_id=${selectedTask}` : ''
        }`,
      ),
    );
  };

  useEffect(() => {
    const fetchData = () => {
      dispatch(fetchInfoTask(`${environment.baseApiUrl}/tasks/tasks-features/?project_id=${decodedId}`));
    };
    fetchData();
    let interval;
    if (isMonitoring) {
      interval = setInterval(fetchData, 3000);
    } else {
      clearInterval(interval);
    }

    return () => clearInterval(interval);
  }, [dispatch, isMonitoring]);

  const handleMonitoring = () => {
    setIsMonitoring((prevState) => !prevState);
  };

  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const josmEditorError = CoreModules.useAppSelector((state) => state.task.josmEditorError);
  const downloadSubmissionLoading = CoreModules.useAppSelector((state) => state.task.downloadSubmissionLoading);
  const uploadToJOSM = () => {
    dispatch(
      ConvertXMLToJOSM(
        `${environment.baseApiUrl}/submission/get_osm_xml/${decodedId}`,
        projectInfo.outline_geojson.bbox,
      ),
    );
  };
  const modalStyle = (theme) => ({
    width: '30%',
    height: '24%',
    bgcolor: theme.palette.mode === 'dark' ? '#0A1929' : 'white',
    border: '1px solid ',
    padding: '16px 32px 24px 32px',
  });
  return (
    <>
      <CoreModules.CustomizedModal isOpen={!!josmEditorError} style={modalStyle}>
        <>
          <h3
            style={{
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            Connection with JOSM failed
          </h3>
          <p> Please verify if JOSM is running on your computer and the remote control is enabled.</p>
          <CoreModules.Button
            variant="contained"
            color="error"
            sx={{
              width: '20%',
              height: '20%',
              p: 2,
              display: 'flex !important',
              justifyContent: 'center !important',
              alignItems: 'center !important',
            }}
            onClick={() => {
              dispatch(CoreModules.TaskActions.SetJosmEditorError(null));
            }}
          >
            Close
          </CoreModules.Button>
        </>
      </CoreModules.CustomizedModal>
      <CoreModules.Box
        sx={{
          px: 3,
          py: 1,
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <CoreModules.Box>
          <CoreModules.IconButton
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              width: '80px',
              mb: 2,
            }}
            onClick={() => {
              navigate(-1);
              // setOpen(true);
            }}
            color="info"
          >
            <AssetModules.ArrowBackIcon color="info" sx={{ fontSize: '30px' }} />
            <CoreModules.Typography ml={2} variant="h1">
              Back
            </CoreModules.Typography>
          </CoreModules.IconButton>
          <CoreModules.Typography variant="h1" color="#929db3">
            #{projectInfo?.id}
          </CoreModules.Typography>
          <CoreModules.Typography variant="subtitle1">{projectInfo?.title}</CoreModules.Typography>
        </CoreModules.Box>

        <ProjectInfoCountCard />

        <CoreModules.Box sx={{ display: 'flex', position: 'relative' }}>
          <CoreModules.LoadingButton
            variant="outlined"
            color="error"
            size="small"
            sx={{ width: 'fit-content', height: 'fit-content', mr: 2 }}
            onClick={uploadToJOSM}
          >
            Upload to JOSM
          </CoreModules.LoadingButton>
          <CoreModules.Button
            variant="outlined"
            color="error"
            size="small"
            sx={{ width: 'fit-content', height: 'fit-content' }}
            onClick={handleMonitoring}
          >
            <CoreModules.Box
              sx={{
                background: isMonitoring ? 'green' : 'red',
                width: '15px',
                height: '15px',
                mr: 1,
                borderRadius: '50%',
                ...(isMonitoring && boxStyles),
              }}
            />
            Monitoring
          </CoreModules.Button>
        </CoreModules.Box>
      </CoreModules.Box>
      <CoreModules.Box sx={{ display: 'flex', pb: 2, height: '80vh' }}>
        {/* Project Info side bar */}
        <ProjectInfoSidebar projectId={projectInfo?.id} projectName={projectInfo?.title} taskInfo={taskInfo} />
        <CoreModules.Box
          sx={{
            boxSizing: 'content-box',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
            px: 2,
          }}
        >
          <ProjectInfomap />
          <CoreModules.Box
            sx={{
              display: 'flex',
              flexDirection: 'row',
              justifyContent: 'center',
              gap: 2,
            }}
          >
            <CoreModules.Button variant="outlined" color="error" sx={{ width: 'fit-content' }} onClick={handleConvert}>
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
          </CoreModules.Box>
          <CoreModules.Card>
            {/* <CoreModules.CardContent>
              Lorem ipsum dolor, sit amet consectetur adipisicing elit. Laborum
              atque soluta qui repudiandae molestias quam veritatis iure magnam
              omnis sequi possimus laboriosam, sed error incidunt numquam eius
              unde ducimus voluptatem.
            </CoreModules.CardContent> */}
          </CoreModules.Card>
        </CoreModules.Box>
      </CoreModules.Box>
    </>
  );
};

export default ProjectInfo;
