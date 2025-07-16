import React, { useEffect, useState } from 'react';

import ProjectOverview from '@/components/CreateProject/01-ProjectOverview';
import ProjectDetails from '@/components/CreateProject/02-ProjectDetails';
import UploadSurvey from '@/components/CreateProject/03-UploadSurvey';
import MapData from '@/components/CreateProject/04-MapData';
import SplitTasks from '@/components/CreateProject/05-SplitTasks';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import {
  useHasManagedAnyOrganization,
  useIsAdmin,
  useIsOrganizationAdmin,
  useIsProjectManager,
} from '@/hooks/usePermissions';

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
import {
  CreateDraftProjectService,
  CreateProjectService,
  DeleteProjectService,
  GetBasicProjectDetails,
  OrganisationService,
} from '@/api/CreateProjectService';
import { defaultValues } from '@/components/CreateProject/constants/defaultValues';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import FormFieldSkeletonLoader from '@/components/Skeletons/common/FormFieldSkeleton';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { convertGeojsonToJsonFile, getDirtyFieldValues } from '@/utilfunctions';
import { data_extract_type, task_split_type } from '@/types/enums';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import { DialogTrigger } from '@radix-ui/react-dialog';

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

  const basicProjectDetailsLoading = useAppSelector((state) => state.createproject.basicProjectDetailsLoading);

  const resetReduxState = () => {
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
  };

  useEffect(() => {
    resetReduxState();
    if (!projectId) return;
    dispatch(GetBasicProjectDetails(`${VITE_API_URL}/projects/${projectId}/minimal`));
  }, [projectId]);

  const [toggleEdit, setToggleEdit] = useState(false);
  const createDraftProjectLoading = useAppSelector((state) => state.createproject.createDraftProjectLoading);
  const createProjectLoading = useAppSelector((state) => state.createproject.createProjectLoading);
  const isProjectDeletePending = useAppSelector((state) => state.createproject.isProjectDeletePending);
  const basicProjectDetails = useAppSelector((state) => state.createproject.basicProjectDetails);

  const isAdmin = useIsAdmin();
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();
  const isOrganizationAdmin = useIsOrganizationAdmin(basicProjectDetails?.organisation_id || null);
  const isProjectManager = useIsProjectManager(projectId);

  useEffect(() => {
    if (step < 1 || step > 5 || !values.osm_category) {
      setSearchParams({ step: '1' });
    }
  }, []);

  useEffect(() => {
    if (!basicProjectDetails || !projectId) return;
    reset({ ...defaultValues, ...basicProjectDetails });

    return () => {
      dispatch(CreateProjectActions.SetBasicProjectDetails(null));
    };
  }, [basicProjectDetails]);

  useEffect(() => {
    dispatch(
      OrganisationService(isAdmin ? `${VITE_API_URL}/organisation` : `${VITE_API_URL}/organisation/my-organisations`),
    );
  }, []);

  const formMethods = useForm<z.infer<typeof createProjectValidationSchema>>({
    defaultValues: defaultValues,
    resolver: zodResolver(validationSchema?.[step] || projectOverviewValidationSchema),
  });

  const { handleSubmit, watch, setValue, trigger, formState, reset, getValues } = formMethods;
  const { dirtyFields } = formState;
  const values = watch();

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
    } = values;

    const projectPayload = {
      name,
      short_description,
      description,
      organisation_id,
      outline,
      uploadedAOIFile,
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
      use_odk_collect: data.use_odk_collect,
      osm_category: data.osm_category,
      primary_geom_type: data.primary_geom_type,
      new_geom_type: data.new_geom_type ? data.new_geom_type : data.primary_geom_type,
      task_split_type: data.task_split_type,
      status: 'PUBLISHED',
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

    dispatch(
      CreateProjectService(
        `${VITE_API_URL}/projects/${projectId}`,
        data.id as number,
        projectData,
        data.project_admins,
        file,
        combinedFeaturesCount,
        isEmptyDataExtract,
        navigate,
      ),
    );
  };

  // const saveProject = () => {};

  const deleteProject = async () => {
    if (!projectId) return;
    await dispatch(DeleteProjectService(`${VITE_API_URL}/projects/${projectId}`, navigate));
  };

  const onSubmit = () => {
    if (step === 1 && !projectId) {
      createDraftProject(true);
      return;
    }
    if (step === 5) createProject();

    if (step < 5) setSearchParams({ step: (step + 1).toString() });
  };

  if (
    (!projectId && !hasManagedAnyOrganization) ||
    (projectId && !basicProjectDetailsLoading && !(isProjectManager || isOrganizationAdmin))
  )
    return <Forbidden />;

  return (
    <div className="fmtm-w-full fmtm-h-full">
      <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-w-full">
        <h5>CREATE NEW PROJECT</h5>
        <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
          {projectId && (
            <Dialog>
              <DialogTrigger>
                <Button variant="link-grey" isLoading={isProjectDeletePending}>
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
                  onClick={deleteProject}
                  isLoading={isProjectDeletePending}
                >
                  Delete
                </Button>
              </DialogContent>
            </Dialog>
          )}
          {/* {step > 1 && (
            <Button
              variant="secondary-grey"
              onClick={saveProject}
              disabled={createProjectLoading || basicProjectDetailsLoading || isProjectDeletePending}
            >
              <AssetModules.SaveIcon className="!fmtm-text-base" />
              Save
            </Button>
          )} */}
          <AssetModules.CloseIcon
            className="!fmtm-text-xl hover:fmtm-text-red-medium fmtm-cursor-pointer"
            onClick={() => navigate('/')}
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
              {basicProjectDetailsLoading && projectId ? <FormFieldSkeletonLoader count={4} /> : form?.[step]}
            </div>

            {/* buttons */}
            <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-px-5 fmtm-py-3 fmtm-shadow-2xl">
              {step > 1 && (
                <Button
                  variant="link-grey"
                  onClick={() => setSearchParams({ step: (step - 1).toString() })}
                  disabled={createProjectLoading || basicProjectDetailsLoading || isProjectDeletePending}
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
                        (createDraftProjectLoading.loading && createDraftProjectLoading.continue) ||
                        isProjectDeletePending
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
                    basicProjectDetailsLoading ||
                    isProjectDeletePending
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
