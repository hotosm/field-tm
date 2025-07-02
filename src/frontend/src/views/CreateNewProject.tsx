import StepSwitcher from '@/components/common/StepSwitcher';
import CreateProjectHeader from '@/components/createnewproject/CreateProjectHeader';
import React, { useEffect, useState } from 'react';
import { createProjectSteps } from '@/constants/StepFormConstants';
import ProjectDetailsForm from '@/components/createnewproject/ProjectDetailsForm';
import UploadArea from '@/components/createnewproject/UploadArea';
import DataExtract from '@/components/createnewproject/DataExtract';
import SplitTasks from '@/components/createnewproject/SplitTasks';
import SelectForm from '@/components/createnewproject/SelectForm';
import { useLocation, useNavigate } from 'react-router-dom';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import Prompt from '@/hooks/Prompt';
import { useHasManagedAnyOrganization } from '@/hooks/usePermissions';
import Forbidden from '@/views/Forbidden';

const CreateNewProject = () => {
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();
  if (!hasManagedAnyOrganization) return <Forbidden />;

  const location = useLocation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const isUnsavedChanges = useAppSelector((state) => state.createproject.isUnsavedChanges);
  const canSwitchCreateProjectSteps = useAppSelector((state) => state.createproject.canSwitchCreateProjectSteps);
  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const [geojsonFile, setGeojsonFile] = useState(null);
  const [customDataExtractUpload, setCustomDataExtractUpload] = useState(null);
  const [xlsFormFile, setXlsFormFile] = useState(null);

  useEffect(() => {
    if (location.pathname !== '/create-project' && !projectDetails.name && !projectDetails.odk_central_url) {
      dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
      navigate('/create-project');
    }
  }, [location.pathname]);

  useEffect(() => {
    switch (location.pathname) {
      case '/create-project':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
        break;
      case '/project-area':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 2 }));
        break;
      case '/upload-survey':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 3 }));
        break;
      case '/map-data':
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
      case '/project-area':
        return (
          <UploadArea
            flag="create_project"
            geojsonFile={geojsonFile}
            setGeojsonFile={setGeojsonFile}
            setCustomDataExtractUpload={setCustomDataExtractUpload}
          />
        );
      case '/upload-survey':
        return (
          <SelectForm
            flag="create_project"
            geojsonFile={geojsonFile}
            xlsFormFile={xlsFormFile}
            setXlsFormFile={setXlsFormFile}
          />
        );
      case '/map-data':
        return (
          <DataExtract
            flag="create_project"
            customDataExtractUpload={customDataExtractUpload}
            setCustomDataExtractUpload={setCustomDataExtractUpload}
          />
        );
      case '/split-tasks':
        return (
          <SplitTasks
            flag="create_project"
            setGeojsonFile={setGeojsonFile}
            customDataExtractUpload={customDataExtractUpload}
            xlsFormFile={xlsFormFile}
          />
        );
      default:
        return <ProjectDetailsForm flag="create_project" />;
    }
  };
  return (
    <div className="fmtm-h-full">
      <CreateProjectHeader />
      <Prompt when={isUnsavedChanges} message="Are you sure you want to leave, you have unsaved changes?" />

      <div className="fmtm-h-[calc(100%-64px)]">
        <div className="fmtm-w-full">
          <div>
            <StepSwitcher data={createProjectSteps} flag={'create_project'} switchSteps={canSwitchCreateProjectSteps} />
          </div>
        </div>
        <div className="lg:fmtm-h-[calc(100%-108px)]">{(() => getCreateProjectContent())()}</div>
      </div>
    </div>
  );
};

export default CreateNewProject;
