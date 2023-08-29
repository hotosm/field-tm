import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import CoreModules from '../shared/CoreModules';
import UploadArea from '../components/createproject/UploadArea';
import { useLocation, Link } from 'react-router-dom';
import ProjectDetailsForm from '../components/createproject/ProjectDetailsForm';
import FormSelection from '../components/createproject/FormSelection';
import DefineTasks from '../components/createproject/DefineTasks';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import DataExtract from '../components/createproject/DataExtract';

const CreateProject: React.FC = () => {
  const [geojsonFile, setGeojsonFile] = useState(null);
  const [customFormFile, setCustomFormFile] = useState(null);
  const [customFormInputValue, setCustomFormInputValue] = useState(null);
  const [inputValue, setInputValue] = useState(null);
  const [dataExtractFile, setDataExtractFile] = useState(null);
  const [dataExtractFileValue, setDataExtractFileValue] = useState(null);
  const [lineExtractFile, setLineExtractFile] = useState(null);
  const [lineExtractFileValue, setLineExtractFileValue] = useState(null);
  const dispatch = CoreModules.useAppDispatch();
  const location = useLocation();
  const boxSX = {
    'button:hover': {
      textDecoration: 'none',
    },
  };
  useEffect(() => {
    return () => {
      dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ dimension: 10 }));
      dispatch(CreateProjectActions.SetGenerateProjectQRSuccess(null));
      dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
      dispatch(CreateProjectActions.SetDrawnGeojson(null));
      setGeojsonFile(null);
      setCustomFormFile(null);
      setDataExtractFile(null);
    };
  }, []);

  return (
    <div>
      <CoreModules.Stack
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          position: 'sticky',
          top: 0,
          background: 'white',
          zIndex: 1,
          paddingBottom: '1.5rem',
        }}
      >
        <CoreModules.Typography variant="subtitle2" color={'info'} noWrap sx={{ display: { sm: 'block' } }} ml={'3%'}>
          Create New Project
        </CoreModules.Typography>
        <CoreModules.Stack
          sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'row', mt: 3 }}
        >
          <CoreModules.Box
            sx={{
              height: location.pathname !== '/create-project' ? '8px' : '12px',
              width: '64px',
              background: location.pathname !== '/create-project' ? '#68707F' : '#D73F3F',
              mx: '16px',
              borderRadius: '10px',
            }}
          ></CoreModules.Box>
          <CoreModules.Box
            sx={{
              height: location.pathname !== '/upload-area' ? '8px' : '12px',
              width: '64px',
              background: location.pathname !== '/upload-area' ? '#68707F' : '#D73F3F',
              mx: '16px',
              borderRadius: '10px',
            }}
          ></CoreModules.Box>
          <CoreModules.Box
            sx={{
              height: location.pathname !== '/data-extract' ? '8px' : '12px',
              width: '64px',
              background: location.pathname !== '/data-extract' ? '#68707F' : '#D73F3F',
              mx: '16px',
              borderRadius: '10px',
            }}
          ></CoreModules.Box>
          <CoreModules.Box
            sx={{
              height: location.pathname !== '/define-tasks' ? '8px' : '12px',
              width: '64px',
              background: location.pathname !== '/define-tasks' ? '#68707F' : '#D73F3F',
              mx: '16px',
              borderRadius: '10px',
            }}
          ></CoreModules.Box>
          <CoreModules.Box
            sx={{
              height: location.pathname !== '/select-form' ? '8px' : '12px',
              width: '64px',
              background: location.pathname !== '/select-form' ? '#68707F' : '#D73F3F',
              mx: '16px',
              borderRadius: '10px',
            }}
          ></CoreModules.Box>
          {/* <CoreModules.Box sx={{ height: location.pathname !== '/basemap-selection' ? '8px' : '12px', width: '64px', background: location.pathname !== '/basemap-selection' ? '#68707F' : '#D73F3F', mx: '16px', borderRadius: '10px' }}></CoreModules.Box> */}
        </CoreModules.Stack>
      </CoreModules.Stack>
      <CoreModules.Stack
        sx={{
          paddingLeft: { xs: '1rem', md: '5rem', lg: '12rem' },
          paddingTop: { xs: '1rem', md: '3rem' },
          height: 'auto',
          background: 'white',
        }}
        direction={{ xs: 'column', md: 'row' }}
      >
        <CoreModules.Stack
          direction={{ xs: 'row', md: 'column' }}
          spacing={{ xs: 1, md: 2 }}
          sx={{
            position: { xs: 'sticky', md: 'fixed' },
            top: { xs: 80, md: 'unset' },
            background: { xs: 'white', md: 'unset' },
            zIndex: { xs: 1, md: 'unset' },
            paddingBottom: 2,
            paddingRight: '1rem',
          }}
        >
          {/* Project Details SideBar Button for Creating Project */}
          <Link to="/create-project">
            <CoreModules.Button variant="contained" color="error" disabled={location.pathname !== '/create-project'}>
              Project Details
            </CoreModules.Button>
          </Link>

          {/* END */}

          {/* Upload Area SideBar Button for uploading Area page  */}
          <Link to="/upload-area">
            <CoreModules.Button
              sx={boxSX}
              variant="contained"
              color="error"
              disabled={location.pathname !== '/upload-area'}
            >
              Upload Area
            </CoreModules.Button>
          </Link>
          {/* END */}

          {/* Extract Data SideBar Button for extracting data page  */}
          <Link to="/data-extract">
            <CoreModules.Button
              sx={boxSX}
              variant="contained"
              color="error"
              disabled={location.pathname !== '/data-extract'}
            >
              Data Extract
            </CoreModules.Button>
          </Link>
          {/* END */}

          {/* Define Tasks SideBar Button for define tasks page  */}
          <Link to="/define-tasks">
            <CoreModules.Button
              sx={boxSX}
              variant="contained"
              color="error"
              disabled={location.pathname !== '/define-tasks'}
            >
              Define Tasks
            </CoreModules.Button>
          </Link>
          {/* END */}
          {/* Upload Area SideBar Button for uploading Area page  */}
          <Link to="/select-form">
            <CoreModules.Button
              sx={boxSX}
              variant="contained"
              color="error"
              disabled={location.pathname !== '/select-form'}
            >
              Select Form
            </CoreModules.Button>
          </Link>
          {/* END */}

          {/* Basemap Selection of Project Boundary   */}
          {/* <Link to="/basemap-selection">
            <CoreModules.Button
              sx={boxSX}
              variant="contained"
              color="error"
              disabled={location.pathname !== '/basemap-selection'}
            >
              Basemap Selection
            </CoreModules.Button>
          </Link> */}
          {/* END */}
        </CoreModules.Stack>
        {/* Showing Different Create Project Component When the url pathname changes */}

        {location.pathname === '/create-project' ? <ProjectDetailsForm /> : null}
        {location.pathname === '/upload-area' ? (
          <UploadArea
            inputValue={inputValue}
            setInputValue={setInputValue}
            geojsonFile={geojsonFile}
            setGeojsonFile={setGeojsonFile}
          />
        ) : null}
        {location.pathname === '/define-tasks' ? (
          <DefineTasks geojsonFile={geojsonFile} setGeojsonFile={setGeojsonFile} dataExtractFile={dataExtractFile} />
        ) : null}
        {location.pathname === '/data-extract' ? (
          <DataExtract
            geojsonFile={geojsonFile}
            setGeojsonFile={setGeojsonFile}
            dataExtractFile={dataExtractFile}
            setDataExtractFile={setDataExtractFile}
            dataExtractFileValue={dataExtractFileValue}
            setDataExtractFileValue={setDataExtractFileValue}
            lineExtractFile={lineExtractFile}
            setLineExtractFile={setLineExtractFile}
            lineExtractFileValue={lineExtractFileValue}
            setLineExtractFileValue={setLineExtractFileValue}
          />
        ) : null}
        {location.pathname === '/select-form' ? (
          <FormSelection
            geojsonFile={geojsonFile}
            customFormFile={customFormFile}
            setCustomFormFile={setCustomFormFile}
            customFormInputValue={customFormInputValue}
            setCustomFormInputValue={setCustomFormInputValue}
            dataExtractFile={dataExtractFile}
            lineExtractFile={lineExtractFile}
          />
        ) : null}
        {/* {location.pathname === "/basemap-selection" ? <BasemapSelection /> : null} */}
        {/* END */}
      </CoreModules.Stack>
    </div>
  );
};

export default CreateProject;
