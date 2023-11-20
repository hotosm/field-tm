import axios from 'axios';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import {
  ProjectDetailsModel,
  FormCategoryListModel,
  OrganisationListModel,
} from '../models/createproject/createProjectModel';
import { CommonActions } from '../store/slices/CommonSlice';
import { ValidateCustomFormResponse } from 'store/types/ICreateProject';

const CreateProjectService: Function = (
  url: string,
  payload: any,
  fileUpload: any,
  formUpload: any,
  dataExtractFile: any,
  lineExtractFile: any,
) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.CreateProjectLoading(true));
    dispatch(CommonActions.SetLoading(true));

    const postCreateProjectDetails = async (url, payload, fileUpload, formUpload) => {
      try {
        const postNewProjectDetails = await axios.post(url, payload);
        const resp: ProjectDetailsModel = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.PostProjectDetails(resp));

        if (payload.splitting_algorithm === 'choose_area_as_task') {
          await dispatch(
            UploadAreaService(`${import.meta.env.VITE_API_URL}/projects/${resp.id}/upload_multi_polygon`, fileUpload),
          );
        } else if (payload.splitting_algorithm === 'Use natural Boundary') {
          await dispatch(
            UploadAreaService(`${import.meta.env.VITE_API_URL}/projects/task_split/${resp.id}/`, fileUpload),
          );
        } else {
          await dispatch(
            UploadAreaService(`${import.meta.env.VITE_API_URL}/projects/${resp.id}/upload_multi_polygon`, fileUpload),
          );
          // await dispatch(UploadAreaService(`${import.meta.env.VITE_API_URL}/projects/${resp.id}/upload`, fileUpload, { dimension: payload.dimension }));
        }
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Successfully Created Now Generating QR For Project',
            variant: 'success',
            duration: 2000,
          }),
        );
        if (dataExtractFile) {
          const dataExtractFormData = new FormData();
          dataExtractFormData.append('upload', dataExtractFile);
          const postDataExtract = await axios.post(
            `${import.meta.env.VITE_API_URL}/projects/add_features/?project_id=${resp.id}&feature_type=buildings`,
            dataExtractFormData,
          );
        }
        if (lineExtractFile) {
          const lineExtractFormData = new FormData();
          lineExtractFormData.append('upload', lineExtractFile);
          const postLineExtract = await axios.post(
            `${import.meta.env.VITE_API_URL}/projects/add_features/?project_id=${resp.id}&feature_type=lines`,
            lineExtractFormData,
          );
        }
        await dispatch(
          GenerateProjectQRService(
            `${import.meta.env.VITE_API_URL}/projects/${resp.id}/generate`,
            payload,
            formUpload,
            dataExtractFile,
          ),
        );

        dispatch(CommonActions.SetLoading(false));
        dispatch(CreateProjectActions.CreateProjectLoading(true));
      } catch (error: any) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(CreateProjectActions.CreateProjectLoading(true));

        // Added Snackbar toast for error message
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail) || 'Something went wrong.',
            variant: 'error',
            duration: 2000,
          }),
        );
        //END
        dispatch(CreateProjectActions.CreateProjectLoading(false));
      } finally {
        dispatch(CreateProjectActions.CreateProjectLoading(false));
      }
    };

    await postCreateProjectDetails(url, payload, fileUpload, formUpload);
  };
};
const FormCategoryService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetFormCategoryLoading(true));

    const getFormCategoryList = async (url) => {
      try {
        const getFormCategoryListResponse = await axios.get(url);
        const resp: FormCategoryListModel = getFormCategoryListResponse.data;
        dispatch(CreateProjectActions.GetFormCategoryList(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GetFormCategoryListLoading(false));
      }
    };

    await getFormCategoryList(url);
  };
};
const UploadAreaService: Function = (url: string, filePayload: any, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.UploadAreaLoading(true));
    const postUploadArea = async (url, filePayload, payload) => {
      try {
        const areaFormData = new FormData();
        areaFormData.append('upload', filePayload);
        if (payload?.dimension) {
          areaFormData.append('dimension', payload?.dimension);
        }
        const postNewProjectDetails = await axios.post(url, areaFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        // const resp: UploadAreaDetailsModel = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.UploadAreaLoading(false));
        await dispatch(CreateProjectActions.PostUploadAreaSuccess(postNewProjectDetails.data));
      } catch (error: any) {
        console.log(error, 'error');
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail) || 'Something Went Wrong.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.UploadAreaLoading(false));
      }
    };

    await postUploadArea(url, filePayload, payload);
  };
};
const GenerateProjectQRService: Function = (url: string, payload: any, formUpload: any, dataExtractFile: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GenerateProjectQRLoading(true));
    dispatch(CommonActions.SetLoading(true));

    const postUploadArea = async (url, payload: any, formUpload) => {
      // debugger;
      console.log(formUpload, 'formUpload');
      console.log(payload, 'payload');
      try {
        const isPolygon = payload.data_extractWays === 'Polygon';
        const generateApiFormData = new FormData();
        if (payload.form_ways === 'custom_form') {
          generateApiFormData.append('extract_polygon', isPolygon.toString());
          generateApiFormData.append('upload', formUpload);
          if (dataExtractFile) {
            generateApiFormData.append('data_extracts', dataExtractFile);
          }
        } else {
          generateApiFormData.append('extract_polygon', isPolygon.toString());
          if (dataExtractFile) {
            generateApiFormData.append('data_extracts', dataExtractFile);
          }
        }
        const postNewProjectDetails = await axios.post(url, generateApiFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        const resp: string = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.GenerateProjectQRLoading(false));
        dispatch(CommonActions.SetLoading(false));
        await dispatch(CreateProjectActions.GenerateProjectQRSuccess(resp));
      } catch (error: any) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail),
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.GenerateProjectQRLoading(false));
      }
    };

    await postUploadArea(url, payload, formUpload);
  };
};

const OrganisationService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetOrganisationListLoading(true));

    const getOrganisationList = async (url) => {
      try {
        const getOrganisationListResponse = await axios.get(url);
        const resp: OrganisationListModel = getOrganisationListResponse.data;
        dispatch(CreateProjectActions.GetOrganisationList(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GetOrganizationListLoading(false));
      }
    };

    await getOrganisationList(url);
  };
};

const UploadCustomXLSFormService: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.UploadCustomXLSFormLoading(true));

    const postUploadCustomXLSForm = async (url, payload) => {
      try {
        const customXLSFormData = new FormData();
        customXLSFormData.append('upload', payload[0]);
        const postCustomXLSForm = await axios.post(url, customXLSFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        await dispatch(CreateProjectActions.UploadCustomXLSFormLoading(false));
        await dispatch(CreateProjectActions.UploadCustomXLSFormSuccess(postCustomXLSForm.data));
      } catch (error: any) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error.response.data.detail) || 'Something Went Wrong',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.UploadCustomXLSFormLoading(false));
      }
    };

    await postUploadCustomXLSForm(url, payload);
  };
};

const GenerateProjectLog: Function = (url: string, params: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GenerateProjectLogLoading(true));

    const getGenerateProjectLog = async (url, params) => {
      try {
        const getGenerateProjectLogResponse = await axios.get(url, { params });
        const resp: OrganisationListModel = getGenerateProjectLogResponse.data;
        dispatch(CreateProjectActions.SetGenerateProjectLog(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GenerateProjectLogLoading(false));
      }
    };

    await getGenerateProjectLog(url, params);
  };
};
const GetDividedTaskFromGeojson: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(true));

    const getDividedTaskFromGeojson = async (url, payload) => {
      try {
        const dividedTaskFormData = new FormData();
        dividedTaskFormData.append('upload', payload.geojson);
        dividedTaskFormData.append('dimension', payload.dimension);
        const getGetDividedTaskFromGeojsonResponse = await axios.post(url, dividedTaskFormData);
        const resp: OrganisationListModel = getGetDividedTaskFromGeojsonResponse.data;
        dispatch(CreateProjectActions.SetDividedTaskGeojson(resp));
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      } catch (error) {
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      }
    };

    await getDividedTaskFromGeojson(url, payload);
  };
};

const GetIndividualProjectDetails: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(true));

    const getIndividualProjectDetails = async (url, payload) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.get(url, { params: payload });
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        const formattedOutlineGeojson = { type: 'FeatureCollection', features: [{ ...resp.outline_geojson, id: 1 }] };
        const modifiedResponse = {
          ...resp,
          name: resp.project_info?.name,
          description: resp.project_info?.description,
          short_description: resp.project_info?.short_description,
          outline_geojson: formattedOutlineGeojson,
        };

        dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      } catch (error) {
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      }
    };

    await getIndividualProjectDetails(url, payload);
  };
};

const TaskSplittingPreviewService: Function = (
  url: string,
  fileUpload: any,
  no_of_buildings: string,
  isCustomDataExtract: boolean,
) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(true));

    const getTaskSplittingGeojson = async (url, fileUpload, isCustomDataExtract) => {
      try {
        const taskSplittingFileFormData = new FormData();
        taskSplittingFileFormData.append('upload', fileUpload);
        taskSplittingFileFormData.append('no_of_buildings', no_of_buildings);
        taskSplittingFileFormData.append('has_data_extracts', isCustomDataExtract);

        const getTaskSplittingResponse = await axios.post(url, taskSplittingFileFormData);
        const resp: OrganisationListModel = getTaskSplittingResponse.data;
        if (resp?.features && resp?.features.length < 1) {
          // Don't update geometry if splitting failed
          // TODO display error to user, perhaps there is not osm data here?
          return;
        }
        dispatch(CreateProjectActions.GetTaskSplittingPreview(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(false));
      } finally {
        dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(false));
      }
    };

    await getTaskSplittingGeojson(url, fileUpload, isCustomDataExtract);
  };
};
const PatchProjectDetails: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(true));

    const patchProjectDetails = async (url, payload) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.patch(url, payload);
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        dispatch(CreateProjectActions.SetPatchProjectDetails(resp));
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Successfully Edited',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
      }
    };

    await patchProjectDetails(url, payload);
  };
};
const PostFormUpdate: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPostFormUpdateLoading(true));

    const postFormUpdate = async (url, payload) => {
      try {
        const formFormData = new FormData();
        formFormData.append('project_id', payload.project_id);
        if (payload.category) {
          formFormData.append('category', payload.category);
        }
        if (payload.upload) {
          formFormData.append('upload', payload.upload);
        }
        const postFormUpdateResponse = await axios.post(url, formFormData);
        const resp: ProjectDetailsModel = postFormUpdateResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        // dispatch(CreateProjectActions.SetPostFormUpdate(resp));
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Form Successfully Updated',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error.response.data.detail,
            variant: 'success',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
      }
    };

    await postFormUpdate(url, payload);
  };
};
const EditProjectBoundaryService: Function = (url: string, geojsonUpload: any, dimension: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(true));

    const postFormUpdate = async (url, geojsonUpload, dimension) => {
      try {
        const editBoundaryFormData = new FormData();
        editBoundaryFormData.append('upload', geojsonUpload);
        if (dimension) {
          editBoundaryFormData.append('dimension', dimension);
        }
        const postBoundaryUpdateResponse = await axios.post(url, editBoundaryFormData);
        const resp: unknown = postBoundaryUpdateResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        // dispatch(CreateProjectActions.SetPostFormUpdate(resp));
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Boundary Successfully Updated',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
      }
    };

    await postFormUpdate(url, geojsonUpload, dimension);
  };
};

const ValidateCustomForm: Function = (url: string, formUpload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.ValidateCustomFormLoading(true));

    const validateCustomForm = async (url: any, formUpload: any) => {
      try {
        const formUploadFormData = new FormData();
        formUploadFormData.append('form', formUpload);

        const getTaskSplittingResponse = await axios.post(url, formUploadFormData);
        const resp: ValidateCustomFormResponse = getTaskSplittingResponse.data;
        dispatch(CreateProjectActions.ValidateCustomForm(resp));
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(resp.message),
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message:
              JSON.stringify(`${error.response.data.message}, ${error.response.data.possible_reason}`) ||
              'Something Went Wrong',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
      } finally {
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
      }
    };

    await validateCustomForm(url, formUpload);
  };
};
export {
  UploadAreaService,
  CreateProjectService,
  FormCategoryService,
  GenerateProjectQRService,
  OrganisationService,
  UploadCustomXLSFormService,
  GenerateProjectLog,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
  GetIndividualProjectDetails,
  PatchProjectDetails,
  PostFormUpdate,
  EditProjectBoundaryService,
  ValidateCustomForm,
};
