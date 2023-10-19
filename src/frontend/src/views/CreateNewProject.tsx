import StepSwitcher from '../components/common/StepSwitcher';
import CreateProjectHeader from '../components/createnewproject/CreateProjectHeader';
import React, { useEffect, useState } from 'react';
import { createProjectSteps } from '../constants/StepFormConstants';
import ProjectDetailsForm from '../components/createnewproject/ProjectDetailsForm';
import UploadArea from '../components/createnewproject/UploadArea';
import DataExtract from '../components/createnewproject/DataExtract';
import SplitTasks from '../components/createnewproject/SplitTasks';
import SelectForm from '../components/createnewproject/SelectForm';
import { useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { CommonActions } from '.././store/slices/CommonSlice';
import { useAppSelector } from '../types/reduxTypes';
import Prompt from '../hooks/Prompt';
const CreateNewProject = () => {
  const location = useLocation();
  const dispatch = useDispatch();

  const isUnsavedChanges = useAppSelector((state) => state.createproject.isUnsavedChanges);
  const [geojsonFile, setGeojsonFile] = useState(null);
  const [customLineUpload, setCustomLineUpload] = useState(null);
  const [customPolygonUpload, setCustomPolygonUpload] = useState(null);
  const [customFormFile, setCustomFormFile] = useState(null);
  useEffect(() => {
    switch (location.pathname) {
      case '/create-project':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
        break;
      case '/upload-area':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 2 }));
        break;
      case '/select-form':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 3 }));
        break;
      case '/data-extract':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 4 }));
        break;
      case '/split-tasks':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 5 }));
        break;
      default:
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
        break;
    }
  }, [location.pathname]);

  const getCreateProjectContent = (): JSX.Element => {
    switch (location.pathname) {
      case '/create-project':
        return <ProjectDetailsForm flag="create_project" />;
      case '/upload-area':
        return <UploadArea flag="create_project" geojsonFile={geojsonFile} setGeojsonFile={setGeojsonFile} />;
      case '/select-form':
        return (
          <SelectForm
            flag="create_project"
            geojsonFile={geojsonFile}
            customFormFile={customFormFile}
            setCustomFormFile={setCustomFormFile}
          />
        );
      case '/data-extract':
        return (
          <DataExtract
            flag="create_project"
            customLineUpload={customLineUpload}
            setCustomLineUpload={setCustomLineUpload}
            customPolygonUpload={customPolygonUpload}
            setCustomPolygonUpload={setCustomPolygonUpload}
          />
        );
      case '/split-tasks':
        return (
          <SplitTasks
            flag="create_project"
            geojsonFile={geojsonFile}
            setGeojsonFile={setGeojsonFile}
            customLineUpload={customLineUpload}
            customPolygonUpload={customPolygonUpload}
            customFormFile={customFormFile}
          />
        );
      default:
        return <ProjectDetailsForm flag="create_project" />;
    }
  };
  return (
    <div>
      <CreateProjectHeader />
      <Prompt when={isUnsavedChanges} message="Are you sure you want to leave, you have unsaved changes?" />

      <div className="fmtm-min-h-[72vh] fmtm-bg-gray-100 fmtm-box-border fmtm-border-[1px] fmtm-border-t-white fmtm-border-t-[0px]">
        <div className=" fmtm-w-full">
          <div>
            <StepSwitcher data={createProjectSteps} flag={'create_project'} />
          </div>
        </div>
        <div className="fmtm-mx-5 fmtm-mb-5">{(() => getCreateProjectContent())()}</div>
      </div>
    </div>
  );
};

export default CreateNewProject;
