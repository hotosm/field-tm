import React, { useEffect, useState } from 'react';
import ProjectTypeSelector from '@/components/CreateProject/00-ProjectTypeSelector';
import ProjectOverview from '@/components/CreateProject/01-ProjectOverview';
import ProjectDetails from '@/components/CreateProject/02-ProjectDetails';
import UploadSurvey from '@/components/CreateProject/03-UploadSurvey';
import MapData from '@/components/CreateProject/04-MapData';
import SplitTasks from '@/components/CreateProject/05-SplitTasks';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Stepper from '@/components/CreateProject/Stepper';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import Map from '@/components/CreateProject/Map';
import {
  createProjectValidationSchema,
  projectOverviewValidationSchema,
  mapDataValidationSchema,
  projectDetailsValidationSchema,
  splitTasksValidationSchema,
  uploadSurveyValidationSchema,
} from '@/components/CreateProject/validation';
import { z } from 'zod/v4';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { CreateDraftProjectService, CreateProjectService } from '@/api/CreateProjectService';
import { defaultValues } from '@/components/CreateProject/constants/defaultValues';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import FormFieldSkeletonLoader from '@/components/Skeletons/common/FormFieldSkeleton';
import { convertGeojsonToJsonFile, getDirtyFieldValues } from '@/utilfunctions';
import { data_extract_type, field_mapping_app, task_split_type } from '@/types/enums';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import { DialogTrigger } from '@radix-ui/react-dialog';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useDeleteProjectMutation, useGetProjectQuery } from '@/api/project';
import { useUploadProjectXlsformMutation } from '@/api/central';
import { FileType } from '@/types';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const validationSchema = {
  1: projectOverviewValidationSchema,
  2: projectDetailsValidationSchema,
  3: uploadSurveyValidationSchema,
  4: mapDataValidationSchema,
  5: splitTasksValidationSchema,
};

const CreateProject = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const params = useParams();
  const projectId = params.id ? +params.id : null;
  const [searchParams, setSearchParams] = useSearchParams();
  const step = Number(searchParams.get('step'));

  const [toggleEdit, setToggleEdit] = useState(false);
  const createDraftProjectLoading = useAppSelector((state) => state.createproject.createDraftProjectLoading);
  const createProjectLoading = useAppSelector((state) => state.createproject.createProjectLoading);
  const isProjectDeletePending = useAppSelector((state) => state.createproject.isProjectDeletePending);

  const { data: projectDetails, isLoading: isProjectLoading } = useGetProjectQuery({
    project_id: projectId!,
    options: { queryKey: ['get-project', projectId], enabled: !!projectId },
  });

  const formMethods = useForm<z.infer<typeof createProjectValidationSchema>>({
    defaultValues: defaultValues,
    resolver: zodResolver(validationSchema?.[step] || projectOverviewValidationSchema),
  });

  const { handleSubmit, watch, setValue, trigger, formState, reset, getValues, setError } = formMethods;
  const { dirtyFields, errors } = formState;
  const values = watch();

  useEffect(() => {
    if (!projectId) {
      setSearchParams({ step: '0' });
    } else if (projectId && (step < 0 || step > 5 || !values.osm_category)) {
      setSearchParams({ step: '1' });
    }
  }, []);

  useEffect(() => {
    if (!projectDetails || !projectId) return;
    const { id, project_name, description, outline, hashtags, field_mapping_app } = projectDetails;
    reset({
      ...defaultValues,
      id,
      project_name,
      description,
      outline,
      hashtags,
      field_mapping_app,
    });
  }, [projectDetails]);

  const form = {
    1: <ProjectOverview />,
    2: <ProjectDetails />,
    3: <UploadSurvey />,
    4: <MapData />,
    5: <SplitTasks />,
  };

  const createDraftProject = async (continueToNextStep: boolean) => {
    const isValidationSuccess = await trigger(undefined, { shouldFocus: true });

    if (!isValidationSuccess) return;
    const { project_name, description, outline, merge, field_mapping_app } = values;

    const projectPayload = {
      project_name,
      description,
      outline,
      merge,
      field_mapping_app,
    };

    dispatch(
      CreateDraftProjectService(`${VITE_API_URL}/projects/stub`, { projectPayload }, navigate, continueToNextStep),
    );
  };

  const createProject = async () => {
    const data = getValues();
    const { project_name, description } = data;

    // retrieve updated fields from project overview
    const dirtyValues = getDirtyFieldValues({ project_name, description }, dirtyFields);

    const projectData = {
      ...dirtyValues,
      visibility: data.visibility,
      hashtags: data.hashtags,
      custom_tms_url: data.custom_tms_url,
      per_task_instructions: data.per_task_instructions,
      osm_category: data.osm_category,
      primary_geom_type: data.primary_geom_type,
      new_geom_type: data.new_geom_type ? data.new_geom_type : data.primary_geom_type,
      task_split_type: data.task_split_type,
      status: 'PUBLISHED',
      field_mapping_app: data.field_mapping_app,
    };

    if (data.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM) {
      projectData.task_num_buildings = data.task_num_buildings;
    } else {
      projectData.task_split_dimension = data.task_split_dimension;
    }

    const taskSplitGeojsonFile = convertGeojsonToJsonFile(
      data.splitGeojsonByAlgorithm || data.splitGeojsonBySquares || data.outline,
      'task',
    );
    const dataExtractGeojsonFile = convertGeojsonToJsonFile(data.dataExtractGeojson, 'extract');

    const file = { taskSplitGeojsonFile, dataExtractGeojsonFile };
    const combinedFeaturesCount = data.dataExtractGeojson?.features?.length ?? 0;
    const isEmptyDataExtract = data.dataExtractType === data_extract_type.NONE;

    dispatch(
      CreateProjectService(
        `${VITE_API_URL}/projects/${projectId}`,
        data.id as number,
        projectData,
        file,
        combinedFeaturesCount,
        isEmptyDataExtract,
        navigate,
      ),
    );
  };

  const { mutate: deleteProjectMutate, isPending: isProjectDeleting } = useDeleteProjectMutation({
    onSuccess: () => {
      dispatch(
        CommonActions.SetSnackBar({
          message: `Project ${projectId} deleted successfully`,
          variant: 'success',
        }),
      );
      navigate('/');
    },
    onError: ({ response }) => {
      if (response?.status === 404) {
        dispatch(
          CommonActions.SetSnackBar({
            message: `Project ${projectId} already deleted`,
            variant: 'error',
          }),
        );
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: `Failed to delete project ${projectId}`,
            variant: 'error',
          }),
        );
      }
      navigate('/');
    },
  });

  const { mutate: uploadProjectXlsformMutate, isPending: isUploadProjectXlsformPending } =
    useUploadProjectXlsformMutation({
      onSuccess: ({ data }) => {
        setSearchParams({ step: (step + 1).toString() });
        setValue('isFormValidAndUploaded', true);
        dispatch(
          CommonActions.SetSnackBar({ message: data?.message || 'XLSForm uploaded successfully', variant: 'success' }),
        );
      },
      onError: ({ response }) => {
        setError('xlsFormFile', { message: response?.data?.detail });
        setValue('isFormValidAndUploaded', false);
        dispatch(
          CommonActions.SetSnackBar({
            message: response?.data?.detail || 'Failed to upload XLSForm form',
          }),
        );
      },
    });

  const uploadXlsformFile = (file: FileType[]) => {
    // Derive use_odk_collect from field_mapping_app (ODK projects use ODK Collect)
    const values = getValues();
    const formData = new FormData();
    formData.append('xlsform_upload', file?.[0]?.file);

    uploadProjectXlsformMutate({
      payload: formData,
      params: {
        project_id: +projectId!,
        use_odk_collect: values.field_mapping_app === field_mapping_app.ODK,
        need_verification_fields: values.needVerificationFields,
        mandatory_photo_upload: values.mandatoryPhotoUpload,
        default_language: values.default_language,
      },
    });
  };

  const onSubmit = () => {
    if (step === 1 && !projectId) {
      createDraftProject(true);
      return;
    }

    if (step === 3 && !values.isFormValidAndUploaded) {
      uploadXlsformFile(values.xlsFormFile);
      return;
    }

    if (step === 5) createProject();

    if (step < 5) setSearchParams({ step: (step + 1).toString() });
  };

  const onError = (validationErrors: any) => {
    // Get the first error message to show to the user
    const errorMessages: string[] = [];

    // Collect all error messages
    Object.keys(validationErrors).forEach((field) => {
      const error = validationErrors[field];
      if (error?.message) {
        errorMessages.push(error.message);
      } else if (typeof error === 'string') {
        errorMessages.push(error);
      } else if (error?.type === 'required') {
        // Handle Zod required field errors
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
        errorMessages.push(`${fieldName} is required`);
      } else if (error?.code === 'invalid_type') {
        // Handle Zod type errors (e.g., "expected string, received undefined")
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
        const expected = error.expected || 'value';
        const received = error.received || 'undefined';
        errorMessages.push(`${fieldName}: expected ${expected}, received ${received}`);
      }
    });

    // Show a user-friendly error message
    if (errorMessages.length > 0) {
      const message =
        errorMessages.length === 1 ? errorMessages[0] : `Please fix the following errors: ${errorMessages.join(', ')}`;

      dispatch(
        CommonActions.SetSnackBar({
          message,
          variant: 'error',
        }),
      );
    } else {
      // Fallback message if we can't parse the errors
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Please check the form for errors before continuing',
          variant: 'error',
        }),
      );
    }
  };

  /* Project type / mapping app selector */
  if (step === 0 && !projectId) {
    return (
      <div className="fmtm-w-full fmtm-h-full">
        <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-w-full">
          <h5>CREATE NEW PROJECT</h5>
          <AssetModules.CloseIcon
            className="!fmtm-text-xl hover:fmtm-text-red-medium fmtm-cursor-pointer"
            onClick={() => navigate('/explore')}
          />
        </div>
        <FormProvider {...formMethods}>
          <ProjectTypeSelector />
        </FormProvider>
      </div>
    );
  }

  return (
    <div className="fmtm-w-full fmtm-h-full">
      <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-w-full">
        <h5>CREATE NEW PROJECT - {values.field_mapping_app}</h5>
        <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
          {projectId && (
            <Dialog>
              <DialogTrigger>
                <Button variant="link-grey" isLoading={isProjectDeleting}>
                  <AssetModules.DeleteIcon className="!fmtm-text-base" />
                  Delete Project
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Do you want to delete this draft project?</DialogTitle>
                </DialogHeader>
                <Button
                  variant="primary-red"
                  className="fmtm-ml-auto fmtm-mt-5"
                  onClick={() => deleteProjectMutate({ project_id: +projectId! })}
                  isLoading={isProjectDeleting}
                >
                  Delete
                </Button>
              </DialogContent>
            </Dialog>
          )}
          {/* Button to return to mapping app selection page */}
          {!projectId && (
            <Button
              variant="link-grey"
              onClick={() => setSearchParams({ step: '0' })}
              disabled={createProjectLoading || isProjectLoading || isProjectDeletePending}
              className="!fmtm-py-0"
            >
              <AssetModules.ArrowBackIosIcon className="!fmtm-text-sm" />
              Change App
            </Button>
          )}
          <AssetModules.CloseIcon
            className="!fmtm-text-xl hover:fmtm-text-red-medium fmtm-cursor-pointer"
            onClick={() => navigate('/explore')}
          />
        </div>
      </div>

      <div
        className={`sm:fmtm-grid fmtm-grid-rows-[auto_1fr] lg:fmtm-grid-rows-1 fmtm-grid-cols-12 fmtm-w-full ${step > 1 || projectId ? 'fmtm-h-[calc(100%-2.8rem)]' : 'fmtm-h-[calc(100%-2rem)]'} fmtm-gap-2 lg:fmtm-gap-5 fmtm-mt-2`}
      >
        {/* stepper container */}
        <div className="fmtm-col-span-12 lg:fmtm-col-span-3 fmtm-h-fit lg:fmtm-h-full fmtm-bg-white fmtm-rounded-xl">
          <Stepper step={step} toggleStep={(value) => setSearchParams({ step: value.toString() })} />
        </div>

        {/* form container */}
        <FormProvider {...formMethods}>
          <form
            onSubmit={handleSubmit(onSubmit, onError)}
            className="fmtm-flex fmtm-flex-col fmtm-col-span-12 sm:fmtm-col-span-7 lg:fmtm-col-span-5 sm:fmtm-h-full fmtm-overflow-y-hidden fmtm-rounded-xl fmtm-bg-white fmtm-my-2 sm:fmtm-my-0"
          >
            <div className="fmtm-flex-1 fmtm-overflow-y-scroll scrollbar fmtm-px-10 fmtm-py-8">
              {isProjectLoading && projectId ? <FormFieldSkeletonLoader count={4} /> : form?.[step]}
            </div>

            {/* buttons */}
            <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-px-5 fmtm-py-3 fmtm-shadow-2xl">
              {step > 1 && (
                <Button
                  variant="link-grey"
                  onClick={() => setSearchParams({ step: (step - 1).toString() })}
                  disabled={createProjectLoading || isProjectLoading || isProjectDeleting}
                >
                  <AssetModules.ArrowBackIosIcon className="!fmtm-text-sm" /> Previous
                </Button>
              )}
              <>
                {step === 1 &&
                  (!projectId ? (
                    <Button
                      variant="secondary-grey"
                      onClick={() => createDraftProject(false)}
                      isLoading={createDraftProjectLoading.loading && !createDraftProjectLoading.continue}
                      disabled={
                        (createDraftProjectLoading.loading && createDraftProjectLoading.continue) || isProjectDeleting
                      }
                    >
                      Save & Exit
                    </Button>
                  ) : (
                    <span></span>
                  ))}
                <Button
                  variant="primary-grey"
                  type="submit"
                  disabled={
                    (createDraftProjectLoading.loading && !createDraftProjectLoading.continue) ||
                    isProjectLoading ||
                    isProjectDeleting ||
                    isUploadProjectXlsformPending
                  }
                  isLoading={
                    (createDraftProjectLoading.loading && createDraftProjectLoading.continue) || createProjectLoading
                  }
                >
                  {step === 5 ? 'Submit' : step === 1 && !projectId ? 'Save & Continue' : 'Next'}
                  <AssetModules.ArrowForwardIosIcon className="!fmtm-text-sm !fmtm-ml-auto" />
                </Button>
              </>
            </div>
          </form>
        </FormProvider>

        {/* map container */}
        <div className="fmtm-col-span-12 sm:fmtm-col-span-5 lg:fmtm-col-span-4 fmtm-h-[20rem] sm:fmtm-h-full fmtm-rounded-xl fmtm-bg-white fmtm-overflow-hidden">
          <Map
            drawToggle={values.uploadAreaSelection === 'draw' && step === 1}
            aoiGeojson={values.outline}
            extractGeojson={values.dataExtractGeojson}
            splitGeojson={values.splitGeojsonBySquares || values.splitGeojsonByAlgorithm}
            onDraw={
              values.outline || values.uploadAreaSelection === 'upload_file'
                ? null
                : (geojson) => {
                    setValue('outline', JSON.parse(geojson));
                    setValue('uploadedAOIFile', []);
                  }
            }
            onModify={
              toggleEdit && values.outline && step === 1
                ? (geojson) => {
                    setValue('outline', JSON.parse(geojson));

                    if (values.customDataExtractFile) setValue('customDataExtractFile', []);
                    if (values.dataExtractGeojson) setValue('dataExtractGeojson', null);

                    if (values.splitGeojsonBySquares) setValue('splitGeojsonBySquares', null);
                    if (values.splitGeojsonByAlgorithm) setValue('splitGeojsonByAlgorithm', null);
                  }
                : null
            }
            toggleEdit={toggleEdit}
            setToggleEdit={step === 1 && !projectId ? setToggleEdit : undefined}
            getAOIArea={(area) => {
              if (values.outline && area !== values.outlineArea) setValue('outlineArea', area);
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default CreateProject;
