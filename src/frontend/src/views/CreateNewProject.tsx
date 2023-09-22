import StepSwitcher from '../components/common/StepSwitcher';
import CreateProjectHeader from '../components/createnewproject/CreateProjectHeader';
import React, { useEffect } from 'react';
import { createProjectSteps } from '../constants/StepFormConstants';
import CoreModules from '../shared/CoreModules.js';
import ProjectDetailsForm from '../components/createnewproject/ProjectDetailsForm';
import UploadArea from '../components/createnewproject/UploadArea';
import DataExtract from '../components/createnewproject/DataExtract';
import SplitTasks from '../components/createnewproject/SplitTasks';
import SelectForm from '../components/createnewproject/SelectForm';
import { useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { CommonActions } from '.././store/slices/CommonSlice';

const CreateNewProject = () => {
  const location = useLocation();
  const dispatch = useDispatch();

  useEffect(() => {
    switch (location.pathname) {
      case '/create-project':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
        break;
      case '/upload-area':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 2 }));
        break;
      case '/data-extract':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 3 }));
        break;
      case '/define-tasks':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 4 }));
        break;
      case '/select-form':
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 5 }));
        break;
      default:
        dispatch(CommonActions.SetCurrentStepFormStep({ flag: 'create_project', step: 1 }));
        break;
    }
  }, [location.pathname]);

  // const currentStep = CoreModules.useAppSelector((state) => state.common.currentStepFormStep.create_project);
  const getCreateProjectContent = (): JSX.Element => {
    // switch (currentStep.step) {
    //   case 1:
    //     return <ProjectDetailsForm flag="create_project" />;
    //   case 2:
    //     return <UploadArea flag="create_project" />;
    //   case 3:
    //     return <DataExtract flag="create_project" />;
    //   case 4:
    //     return <SplitTasks flag="create_project" />;
    //   case 5:
    //     return <SelectForm flag="create_project" />;
    //   default:
    //     return <ProjectDetailsForm flag="create_project" />;
    // }
    switch (location.pathname) {
      case '/create-project':
        return <ProjectDetailsForm flag="create_project" />;
      case '/upload-area':
        return <UploadArea flag="create_project" />;
      case '/data-extract':
        return <DataExtract flag="create_project" />;
      case '/define-tasks':
        return <SplitTasks flag="create_project" />;
      case '/select-form':
        return <SelectForm flag="create_project" />;
      default:
        return <ProjectDetailsForm flag="create_project" />;
    }
  };
  return (
    <div>
      <CreateProjectHeader />
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
