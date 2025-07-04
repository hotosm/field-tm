import React, { useEffect, useState } from 'react';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import AssetModules from '@/shared/AssetModules.js';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import DefineTaskValidation from '@/components/createnewproject/validation/DefineTaskValidation';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import {
  CreateProjectService,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
} from '@/api/CreateProjectService';
import { task_split_type } from '@/types/enums';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { taskSplitOptionsType } from '@/store/types/ICreateProject';
import DescriptionSection from '@/components/createnewproject/Description';

const SplitTasks = ({ flag, setGeojsonFile, customDataExtractUpload, xlsFormFile }) => {
  useDocumentTitle('Create Project: Split Tasks');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [disableSubmitButton, setDisableSubmitButton] = useState(true);
  const [combinedFeaturesCount, setCombinedFeaturesCount] = useState(0);

  const taskSplittingMethod = useAppSelector((state) => state.createproject.taskSplittingMethod);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);

  const generateProjectSuccess = useAppSelector((state) => state.createproject.generateProjectSuccess);
  const generateProjectWarning = useAppSelector((state) => state.createproject.generateProjectWarning);
  const generateProjectError = useAppSelector((state) => state.createproject.generateProjectError);
  const projectDetailsResponse = useAppSelector((state) => state.createproject.projectDetailsResponse);
  const dividedTaskGeojson = useAppSelector((state) => state.createproject.dividedTaskGeojson);
  const projectDetailsLoading = useAppSelector((state) => state.createproject.projectDetailsLoading);
  const dividedTaskLoading = useAppSelector((state) => state.createproject.dividedTaskLoading);
  const taskSplittingGeojsonLoading = useAppSelector((state) => state.createproject.taskSplittingGeojsonLoading);
  const isTasksSplit = useAppSelector((state) => state.createproject.isTasksSplit);
  const isFgbFetching = useAppSelector((state) => state.createproject.isFgbFetching);
  const toggleSplittedGeojsonEdit = useAppSelector((state) => state.createproject.toggleSplittedGeojsonEdit);

  const usesDataExtract = !!dataExtractGeojson?.features?.length;

  // convert dataExtractGeojson to file object to upload to /upload-data-extract endpoint
  const dataExtractBlob = new Blob([JSON.stringify(dataExtractGeojson)], { type: 'application/json' });
  const dataExtractGeojsonFile = new File([dataExtractBlob], 'outline.json', { type: 'application/json' });

  useEffect(() => {
    const featureCount = dataExtractGeojson?.features?.length ?? 0;
    // Set combined feature count to send to backend for hard limits
    // NOTE that was called 'combined' as previously we added extra features
    setCombinedFeaturesCount(featureCount);
  }, [dataExtractGeojson]);

  const toggleStep = (step: number, url: string) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
    dispatch(CreateProjectActions.SetToggleSplittedGeojsonEdit(false));
  };

  const checkTasksGeneration = () => {
    if (!taskSplittingMethod) {
      setDisableSubmitButton(true);
      return;
    }

    if (!isTasksSplit.divide_on_square && taskSplittingMethod === task_split_type.DIVIDE_ON_SQUARE) {
      setDisableSubmitButton(true);
      return;
    } else if (
      !isTasksSplit.task_splitting_algorithm &&
      taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM
    ) {
      setDisableSubmitButton(true);
      return;
    }

    setDisableSubmitButton(false);
  };

  useEffect(() => {
    checkTasksGeneration();
  }, [taskSplittingMethod, isTasksSplit]);

  const submission = () => {
    dispatch(CreateProjectActions.SetIsUnsavedChanges(false));
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));

    // Project POST data
    let projectData = {
      name: projectDetails.name,
      short_description: projectDetails.short_description,
      description: projectDetails.description,
      per_task_instructions: projectDetails.per_task_instructions,
      // Use split task areas, or project area if no task splitting
      outline: drawnGeojson,
      odk_central_url: projectDetails.odk_central_url,
      odk_central_user: projectDetails.odk_central_user,
      odk_central_password: projectDetails.odk_central_password,
      primary_geom_type: projectDetails.primaryGeomType,
      new_geom_type: projectDetails.newGeomType ? projectDetails.newGeomType : projectDetails.primaryGeomType,
      task_split_type: taskSplittingMethod,
      // "uploaded_form": projectDetails.uploaded_form,
      hashtags: projectDetails.hashtags,
      custom_tms_url: projectDetails.custom_tms_url,
      visibility: projectDetails.visibility,
      use_odk_collect: projectDetails.use_odk_collect,
      status: 'PUBLISHED',
    };
    // Append osm_category if set
    if (projectDetails.osmFormSelectionName) {
      projectData = { ...projectData, osm_category: projectDetails.osmFormSelectionName };
    }
    // Append extra param depending on task split type
    if (taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM) {
      projectData = { ...projectData, task_num_buildings: projectDetails.average_buildings_per_task };
    } else {
      projectData = { ...projectData, task_split_dimension: projectDetails.dimension };
    }

    // Create file object from generated task areas
    const taskAreaBlob = new Blob([JSON.stringify(dividedTaskGeojson || drawnGeojson)], {
      type: 'application/json',
    });
    // Create a file object from the Blob
    const taskAreaGeojsonFile = new File([taskAreaBlob], 'data.json', { type: 'application/json' });

    dispatch(
      CreateProjectService(
        `${import.meta.env.VITE_API_URL}/projects?org_id=${projectDetails.organisation_id}`,
        projectData,
        taskAreaGeojsonFile,
        xlsFormFile?.file,
        customDataExtractUpload?.file || dataExtractGeojsonFile,
        projectDetails.project_admins as number[],
        combinedFeaturesCount,
        projectDetails.dataExtractType === 'no_data_extract',
      ),
    );
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...formValues }));
    dispatch(CreateProjectActions.SetCanSwitchCreateProjectSteps(true));
  };

  useEffect(() => {
    if (taskSplittingMethod === task_split_type.CHOOSE_AREA_AS_TASK) {
      dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
    }
  }, [taskSplittingMethod]);

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DefineTaskValidation);

  const taskSplitOptions: taskSplitOptionsType[] = [
    {
      name: 'define_tasks',
      value: task_split_type.DIVIDE_ON_SQUARE,
      label: 'Divide into square tasks',
      disabled: formValues.primaryGeomType === 'POLYLINE',
    },
    {
      name: 'define_tasks',
      value: task_split_type.CHOOSE_AREA_AS_TASK,
      label: 'Use uploaded AOI as task areas',
      disabled: false,
    },
    {
      name: 'define_tasks',
      value: task_split_type.TASK_SPLITTING_ALGORITHM,
      label: 'Task Splitting Algorithm',
      disabled: !usesDataExtract || formValues.primaryGeomType === 'POLYLINE',
    },
  ];

  const generateTaskBasedOnSelection = (e) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...formValues }));

    e.preventDefault();
    e.stopPropagation();
    // Create a file object from the project area Blob
    const projectAreaBlob = new Blob([JSON.stringify(drawnGeojson)], { type: 'application/json' });
    const drawnGeojsonFile = new File([projectAreaBlob], 'outline.json', { type: 'application/json' });

    // Create a file object from the data extract Blob
    const dataExtractBlob = new Blob([JSON.stringify(dataExtractGeojson)], { type: 'application/json' });
    const dataExtractFile = new File([dataExtractBlob], 'extract.json', { type: 'application/json' });

    if (taskSplittingMethod === task_split_type.DIVIDE_ON_SQUARE) {
      dispatch(
        GetDividedTaskFromGeojson(`${import.meta.env.VITE_API_URL}/projects/preview-split-by-square`, {
          geojson: drawnGeojsonFile,
          extract_geojson: formValues.dataExtractType === 'osm_data_extract' ? null : dataExtractFile,
          dimension: formValues?.dimension,
        }),
      );
    } else if (taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM) {
      dispatch(
        TaskSplittingPreviewService(
          `${import.meta.env.VITE_API_URL}/projects/task-split`,
          drawnGeojsonFile,
          formValues?.average_buildings_per_task,
          // Only send dataExtractFile if custom extract
          formValues.dataExtractType === 'osm_data_extract' ? null : dataExtractFile,
        ),
      );
    }
  };

  useEffect(() => {
    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    const handleQRGeneration = async () => {
      if (!generateProjectError && generateProjectSuccess) {
        const projectId = projectDetailsResponse?.id;

        if (generateProjectWarning) {
          dispatch(
            CommonActions.SetSnackBar({
              message: generateProjectWarning,
              variant: 'success',
              duration: 20000,
            }),
          );
          // Add 20-second delay to allow backend Entity generation to catch up
          await delay(20000);
        } else {
          dispatch(
            CommonActions.SetSnackBar({
              message: 'Project Generation Completed. Redirecting...',
              variant: 'success',
            }),
          );
          // Add 5-second delay to allow backend Entity generation to catch up
          await delay(5000);
        }

        dispatch(CreateProjectActions.CreateProjectLoading(false));
        navigate(`/project/${projectId}`);
        dispatch(CreateProjectActions.ClearCreateProjectFormData());
        dispatch(CreateProjectActions.SetCanSwitchCreateProjectSteps(false));
      }
    };

    handleQRGeneration();
  }, [generateProjectSuccess, generateProjectError]);

  const downloadSplittedGeojson = () => {
    const blob = new Blob([JSON.stringify(dividedTaskGeojson)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'task_splitted_geojson.geojson';
    a.click();
  };

  const parsedTaskGeojsonCount = dividedTaskGeojson?.features?.length || drawnGeojson?.features?.length || 1;
  const totalSteps = dividedTaskGeojson?.features ? dividedTaskGeojson?.features?.length : parsedTaskGeojsonCount;
  return (
    <>
      <form onSubmit={handleSubmit} className="fmtm-h-full">
        <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
          <DescriptionSection section="Split Tasks" />
          <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
            <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between">
                <div>
                  <RadioButton
                    value={taskSplittingMethod || ''}
                    topic="Select an option to split your project area"
                    options={taskSplitOptions}
                    direction="column"
                    onChangeData={(value) => {
                      handleCustomChange('task_split_type', value);
                      dispatch(CreateProjectActions.SetTaskSplittingMethod(value as task_split_type));
                      if (task_split_type.CHOOSE_AREA_AS_TASK === value) {
                        dispatch(CreateProjectActions.SetIsTasksSplit({ key: 'divide_on_square', value: false }));
                        dispatch(
                          CreateProjectActions.SetIsTasksSplit({ key: 'task_splitting_algorithm', value: false }),
                        );
                      }
                    }}
                    errorMsg={errors.task_split_type}
                    hoveredOption={(hoveredOption) =>
                      dispatch(
                        CreateProjectActions.SetDescriptionToFocus(
                          hoveredOption ? `splittasks-${hoveredOption}` : null,
                        ),
                      )
                    }
                  />
                  <div className="fmtm-mt-5">
                    <p className="fmtm-text-gray-500">
                      Total number of features:{' '}
                      <span className="fmtm-font-bold">{dataExtractGeojson?.features?.length || 0}</span>
                    </p>
                  </div>
                  {taskSplittingMethod === task_split_type.DIVIDE_ON_SQUARE && (
                    <>
                      <div className="fmtm-mt-6 fmtm-flex fmtm-items-center fmtm-gap-4">
                        <p className="fmtm-text-gray-500">Dimension of square in metres: </p>
                        <input
                          type="number"
                          value={formValues.dimension}
                          onChange={(e) => handleCustomChange('dimension', e.target.value)}
                          className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-600 fmtm-h-7 fmtm-w-16 fmtm-px-2 "
                        />
                      </div>
                      {errors.dimension && (
                        <div>
                          <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.dimension}</p>
                        </div>
                      )}
                    </>
                  )}
                  {taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM && (
                    <>
                      <div className="fmtm-mt-6 fmtm-flex fmtm-items-center fmtm-gap-4">
                        <p className="fmtm-text-gray-500">Average number of buildings per task: </p>
                        <input
                          type="number"
                          value={formValues.average_buildings_per_task}
                          onChange={(e) => handleCustomChange('average_buildings_per_task', parseInt(e.target.value))}
                          className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-600 fmtm-h-7 fmtm-w-16 fmtm-px-2 "
                        />
                      </div>
                      {errors.average_buildings_per_task && (
                        <div>
                          <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">
                            {errors.average_buildings_per_task}
                          </p>
                        </div>
                      )}
                    </>
                  )}
                  {(taskSplittingMethod === task_split_type.DIVIDE_ON_SQUARE ||
                    taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM) && (
                    <div className="fmtm-mt-6 fmtm-pb-3">
                      <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
                        <Button
                          variant="primary-red"
                          isLoading={dividedTaskLoading || taskSplittingGeojsonLoading}
                          onClick={generateTaskBasedOnSelection}
                          disabled={
                            (taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM &&
                              !formValues?.average_buildings_per_task) ||
                            isFgbFetching
                              ? true
                              : false
                          }
                        >
                          Click to generate task
                          <AssetModules.SettingsIcon />
                        </Button>
                      </div>
                    </div>
                  )}
                  {(taskSplittingMethod === task_split_type.DIVIDE_ON_SQUARE ||
                    taskSplittingMethod === task_split_type.TASK_SPLITTING_ALGORITHM ||
                    taskSplittingMethod === task_split_type.CHOOSE_AREA_AS_TASK) && (
                    <div>
                      <p className="fmtm-text-gray-500 fmtm-mt-5 fmtm-mb-2">
                        Total number of task: <span className="fmtm-font-bold">{totalSteps}</span>
                      </p>
                      {dividedTaskGeojson && (
                        <Button variant="link-grey" onClick={downloadSplittedGeojson}>
                          <AssetModules.FileDownloadOutlinedIcon />
                          Download split geojson
                        </Button>
                      )}
                    </div>
                  )}
                </div>
                <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
                  <Button
                    variant="secondary-grey"
                    onClick={() => {
                      dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
                      toggleStep(3, '/map-data');
                    }}
                  >
                    PREVIOUS
                  </Button>
                  <Button
                    variant="primary-red"
                    type="submit"
                    isLoading={projectDetailsLoading}
                    disabled={disableSubmitButton}
                  >
                    SUBMIT
                  </Button>
                </div>
              </div>
              <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
                <NewDefineAreaMap
                  splittedGeojson={dividedTaskGeojson}
                  uploadedOrDrawnGeojsonFile={drawnGeojson}
                  buildingExtractedGeojson={dataExtractGeojson}
                  onModify={
                    toggleSplittedGeojsonEdit
                      ? (geojson) => {
                          handleCustomChange('drawnGeojson', geojson);
                          dispatch(CreateProjectActions.SetDividedTaskGeojson(JSON.parse(geojson)));
                          setGeojsonFile(null);
                        }
                      : null
                  }
                  // toggleSplittedGeojsonEdit
                  hasEditUndo
                />
              </div>
            </div>
          </div>
        </div>
      </form>
    </>
  );
};

export default SplitTasks;
