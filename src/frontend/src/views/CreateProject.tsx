import React, { useEffect, useState } from 'react';
import ProjectTypeSelector from '@/components/CreateProject/00-ProjectTypeSelector';
import ProjectOverview from '@/components/CreateProject/01-ProjectOverview';
import ProjectDetails from '@/components/CreateProject/02-ProjectDetails';
import UploadSurvey from '@/components/CreateProject/03-UploadSurvey';
import MapData from '@/components/CreateProject/04-MapData';
import SplitTasks from '@/components/CreateProject/05-SplitTasks';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useHasManagedAnyOrganization, useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';
import Forbidden from '@/views/Forbidden';
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
import { data_extract_type, project_roles, task_split_type } from '@/types/enums';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import { DialogTrigger } from '@radix-ui/react-dialog';
import { CommonActions } from '@/store/slices/CommonSlice';
import isEmpty from '@/utilfunctions/isEmpty';
import { useDeleteProjectMutation, useGetProjectMinimalQuery, useGetProjectUsersQuery } from '@/api/project';
import { useUploadProjectXlsformMutation } from '@/api/central';

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

  const { data: minimalProjectDetails, isLoading: isMinimalProjectLoading } = useGetProjectMinimalQuery({
    project_id: projectId!,
    options: { queryKey: ['get-minimal-project', projectId], enabled: !!projectId },
  });

  const hasManagedAnyOrganization = useHasManagedAnyOrganization();
  const isOrganizationAdmin = useIsOrganizationAdmin(
    minimalProjectDetails ? +minimalProjectDetails?.organisation_id : null,
  );
  const isProjectManager = useIsProjectManager(projectId);

  const formMethods = useForm<z.infer<typeof createProjectValidationSchema>>({
    defaultValues: defaultValues,
    resolver: zodResolver(validationSchema?.[step] || projectOverviewValidationSchema),
  });

  const { handleSubmit, watch, setValue, trigger, formState, reset, getValues, setError } = formMethods;
  const { dirtyFields } = formState;
  const values = watch();

  useEffect(() => {
    if (!projectId) {
      setSearchParams({ step: '0' });
    } else if (projectId && (step < 0 || step > 5 || !values.osm_category)) {
      setSearchParams({ step: '1' });
    }
  }, []);

  useEffect(() => {
    if (!minimalProjectDetails || !projectId) return;
    const {
      id,
      name,
      short_description,
      description,
      organisation_id,
      outline,
      hashtags,
      organisation_name,
      field_mapping_app,
      use_odk_collect,
    } = minimalProjectDetails;
    reset({
      ...defaultValues,
      id,
      name,
      short_description,
      description,
      organisation_id: +organisation_id,
      outline,
      hashtags,
      organisation_name,
      field_mapping_app,
      use_odk_collect,
    });
  }, [minimalProjectDetails]);

  const { data: projectManagers } = useGetProjectUsersQuery({
    project_id: projectId!,
    params: { role: project_roles.PROJECT_MANAGER },
    options: { queryKey: ['get-project-users', project_roles.PROJECT_MANAGER, projectId], enabled: !!projectId },
  });

  // setup project admin select options if project admins are available
  useEffect(() => {
    // only set project_admins value after basic project details are fetched
    if (!projectId || !projectManagers || isEmpty(projectManagers) || isMinimalProjectLoading) return;

    const projectAdminOptions = projectManagers?.map((admin) => ({
      id: admin.user_sub,
      label: admin.username,
      value: admin.user_sub,
    }));
    const project_admins = projectManagers.map((admin) => admin.user_sub);
    dispatch(
      CommonActions.SetPreviousSelectedOptions({
        key: 'project_admins',
        options: projectAdminOptions,
      }),
    );
    setValue('project_admins', project_admins);
  }, [projectManagers, projectId, isMinimalProjectLoading]);

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
    const {
      name,
      short_description,
      description,
      organisation_id,
      project_admins,
      outline,
      uploadedAOIFile,
      odk_central_url,
      odk_central_user,
      odk_central_password,
      merge,
      field_mapping_app,
      use_odk_collect,
    } = values;

    const projectPayload = {
      name,
      short_description,
      description,
      organisation_id,
      outline,
      uploadedAOIFile,
      merge,
      field_mapping_app,
      use_odk_collect,
    };

    let odkPayload: Pick<
      z.infer<typeof createProjectValidationSchema>,
      'odk_central_url' | 'odk_central_user' | 'odk_central_password'
    > | null = null;

    if (values.useDefaultODKCredentials) {
      odkPayload = null;
    } else {
      odkPayload = {
        odk_central_url,
        odk_central_user,
        odk_central_password,
      };
    }

    dispatch(
      CreateDraftProjectService(
        `${VITE_API_URL}/projects/stub`,
        { projectPayload, odkPayload, project_admins },
        navigate,
        continueToNextStep,
      ),
    );
  };

  const createProject = async () => {
    const data = getValues();
    const { name, description, short_description } = data;

    // retrieve updated fields from project overview
    const dirtyValues = getDirtyFieldValues({ name, description, short_description }, dirtyFields);

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

    const file = { taskSplitGeojsonFile, dataExtractGeojsonFile, xlsFormFile: data.xlsFormFile?.file };
    const combinedFeaturesCount = data.dataExtractGeojson?.features?.length ?? 0;
    const isEmptyDataExtract = data.dataExtractType === data_extract_type.NONE;

    // Project admins that are already assigned during draft project creation
    const assignedPMs = projectManagers?.map((pm) => pm.user_sub);

    // Identify Project Admins to remove: those who are currently assigned but not included in the new list
    const pmToRemove = assignedPMs?.filter((pm) => !data.project_admins.includes(pm));

    // Identify Project Admins to assign: those in the new list who are not yet assigned to the project
    const pmToAssign = data.project_admins.filter((pm) => !assignedPMs?.includes(pm));

    dispatch(
      CreateProjectService(
        `${VITE_API_URL}/projects/${projectId}`,
        data.id as number,
        projectData,
        { projectAdminToRemove: pmToRemove || [], projectAdminToAssign: pmToAssign },
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

  const uploadXlsformFile = (file) => {
    // use_odk_collect is from previous step, while needVerificationFields is from this step
    const values = getValues();
    const formData = new FormData();
    formData.append('xlsform', file?.file);

    uploadProjectXlsformMutate({
      payload: formData,
      params: {
        project_id: +projectId!,
        use_odk_collect: values.use_odk_collect,
        need_verification_fields: values.needVerificationFields,
        mandatory_photo_upload: values.mandatoryPhotoUpload,
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

  if (
    (!projectId && !hasManagedAnyOrganization) ||
    (projectId && !isMinimalProjectLoading && !(isProjectManager || isOrganizationAdmin))
  )
    return <Forbidden />;

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
              disabled={createProjectLoading || isMinimalProjectLoading || isProjectDeletePending}
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
            onSubmit={handleSubmit(onSubmit)}
            className="fmtm-flex fmtm-flex-col fmtm-col-span-12 sm:fmtm-col-span-7 lg:fmtm-col-span-5 sm:fmtm-h-full fmtm-overflow-y-hidden fmtm-rounded-xl fmtm-bg-white fmtm-my-2 sm:fmtm-my-0"
          >
            <div className="fmtm-flex-1 fmtm-overflow-y-scroll scrollbar fmtm-px-10 fmtm-py-8">
              {isMinimalProjectLoading && projectId ? <FormFieldSkeletonLoader count={4} /> : form?.[step]}
            </div>

            {/* buttons */}
            <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-px-5 fmtm-py-3 fmtm-shadow-2xl">
              {step > 1 && (
                <Button
                  variant="link-grey"
                  onClick={() => setSearchParams({ step: (step - 1).toString() })}
                  disabled={createProjectLoading || isMinimalProjectLoading || isProjectDeleting}
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
                    isMinimalProjectLoading ||
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
                    setValue('uploadedAOIFile', undefined);
                  }
            }
            onModify={
              toggleEdit && values.outline && step === 1
                ? (geojson) => {
                    setValue('outline', JSON.parse(geojson));

                    if (values.customDataExtractFile) setValue('customDataExtractFile', null);
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
