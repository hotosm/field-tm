import React, { useEffect, useRef } from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import FormGroup from '@mui/material/FormGroup';
import {
  CreateProjectService,
  FormCategoryService,
  GenerateProjectLog,
  ValidateCustomForm,
} from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { Grid, InputLabel, MenuItem, Select } from '@mui/material';
import AssetModules from '../../shared/AssetModules.js';
import useForm from '../../hooks/useForm';
import SelectFormValidation from './validation/SelectFormValidation';
import { CommonActions } from '../../store/slices/CommonSlice';
import LoadingBar from './LoadingBar';
import environment from '../../environment';
import { useAppSelector } from '../../types/reduxTypes';

// import { SelectPicker } from 'rsuite';
let generateProjectLogIntervalCb: any = null;

const FormSelection: React.FC<any> = ({
  customFormFile,
  setCustomFormFile,
  customFormInputValue,
  dataExtractFile,
  lineExtractFile,
  setLineExtractFile,
}) => {
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const navigate = useNavigate();

  const dispatch = CoreModules.useAppDispatch();
  // //dispatch function to perform redux state mutation

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  const selectFormWaysList = ['Use Existing Category', 'Upload a Custom Form'];
  const selectFormWays = selectFormWaysList.map((item) => ({ label: item, value: item }));
  const userDetails: any = CoreModules.useAppSelector((state) => state.login.loginToken);
  // //we use use-selector from redux to get all state of loginToken from login slice

  const generateProjectLog: any = CoreModules.useAppSelector((state) => state.createproject.generateProjectLog);
  // //we use use-selector from redux to get all state of loginToken from login slice
  const generateQrSuccess: any = CoreModules.useAppSelector((state) => state.createproject.generateQrSuccess);
  // //we use use-selector from redux to get all state of loginToken from login slice
  const projectDetailsResponse = CoreModules.useAppSelector((state) => state.createproject.projectDetailsResponse);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  const dividedTaskGeojson = CoreModules.useAppSelector((state) => state.createproject.dividedTaskGeojson);
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice
  const projectDetailsLoading = CoreModules.useAppSelector((state) => state.createproject.projectDetailsLoading);
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice

  // END

  const submission = () => {
    const newDividedTaskGeojson = JSON.stringify(dividedTaskGeojson);
    const parsedNewDividedTaskGeojson = JSON.parse(newDividedTaskGeojson);
    const exparsedNewDividedTaskGeojson = JSON.stringify(parsedNewDividedTaskGeojson);
    var newUpdatedTaskGeojsonFile = new File([exparsedNewDividedTaskGeojson], 'AOI.geojson', {
      type: 'application/geo+json',
    });
    const hashtags = projectDetails.hashtags;
    const arrayHashtag = hashtags
      .split('#')
      .map((item) => item.trim())
      .filter(Boolean);

    // console.log(f,'file F');
    // setGeojsonFile(f);
    dispatch(
      CreateProjectService(
        `${import.meta.env.VITE_API_URL}/projects/create_project`,
        {
          project_info: {
            name: projectDetails.name,
            short_description: projectDetails.short_description,
            description: projectDetails.description,
          },
          author: {
            username: userDetails?.username || 'svcfmtm',
            id: userDetails?.id || 20386219,
          },
          odk_central: {
            odk_central_url: projectDetails.odk_central_url,
            odk_central_user: projectDetails.odk_central_user,
            odk_central_password: projectDetails.odk_central_password,
          },
          // dont send xform_title if upload custom form is selected
          xform_title: projectDetails.form_ways === 'Upload a Form' ? null : projectDetails.xform_title,
          dimension: projectDetails.dimension,
          splitting_algorithm: projectDetails.splitting_algorithm,
          form_ways: projectDetails.form_ways,
          // "uploaded_form": projectDetails.uploaded_form,
          data_extractWays: projectDetails.data_extractWays,
          hashtags: arrayHashtag,
          organisation_id: projectDetails.organisation_id,
        },
        newUpdatedTaskGeojsonFile,
        customFormFile,
        dataExtractFile,
        lineExtractFile,
      ),
    );
    // navigate("/select-form", { replace: true, state: { values: values } });
  };

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
    return () => {
      clearInterval(generateProjectLogIntervalCb);
      generateProjectLogIntervalCb = null;
      dispatch(CreateProjectActions.SetGenerateProjectLog(null));
    };
  }, []);
  // END

  // Fetching form category list
  useEffect(() => {
    if (generateQrSuccess) {
      if (generateProjectLogIntervalCb === null) {
        dispatch(
          GenerateProjectLog(`${import.meta.env.VITE_API_URL}/projects/generate-log/`, {
            project_id: projectDetailsResponse?.id,
            uuid: generateQrSuccess.task_id,
          }),
        );
      }
    }
  }, [generateQrSuccess]);
  useEffect(() => {
    if (generateQrSuccess && generateProjectLog?.status === 'FAILED') {
      clearInterval(generateProjectLogIntervalCb);
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: `QR Generation Failed. ${generateProjectLog?.message}`,
          variant: 'error',
          duration: 10000,
        }),
      );
    } else if (generateQrSuccess && generateProjectLog?.status === 'SUCCESS') {
      clearInterval(generateProjectLogIntervalCb);
      const encodedProjectId = environment.encode(projectDetailsResponse?.id);
      navigate(`/project_details/${encodedProjectId}`);
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'QR Generation Completed.',
          variant: 'success',
          duration: 2000,
        }),
      );
      dispatch(CreateProjectActions.SetGenerateProjectLog(null));
    }
    if (generateQrSuccess && generateProjectLog?.status === 'PENDING') {
      if (generateProjectLogIntervalCb === null) {
        generateProjectLogIntervalCb = setInterval(() => {
          dispatch(
            GenerateProjectLog(`${import.meta.env.VITE_API_URL}/projects/generate-log/`, {
              project_id: projectDetailsResponse?.id,
              uuid: generateQrSuccess.task_id,
            }),
          );
        }, 2000);
      }
    }
  }, [generateQrSuccess, generateProjectLog]);
  // END
  const renderTraceback = (errorText: string) => {
    if (!errorText) {
      return null;
    }

    return errorText.split('\n').map((line, index) => (
      <div key={index} style={{ display: 'flex' }}>
        <span style={{ color: 'gray', marginRight: '1em' }}>{index + 1}.</span>
        <span>{line}</span>
      </div>
    ));
  };
  const divRef = useRef(null);
  useEffect(() => {
    if (!divRef?.current) return;
    const myDiv: HTMLDivElement = divRef?.current;
    myDiv.scrollTop = myDiv?.scrollHeight;
  });

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    SelectFormValidation,
  );
  const parsedTaskGeojsonCount =
    dividedTaskGeojson?.features?.length ||
    JSON?.parse(dividedTaskGeojson)?.features?.length ||
    projectDetails?.areaGeojson?.features?.length;
  const totalSteps = dividedTaskGeojson?.features ? dividedTaskGeojson?.features?.length : parsedTaskGeojsonCount;

  useEffect(() => {
    if (customFormFile) {
      dispatch(ValidateCustomForm(`${import.meta.env.VITE_API_URL}/projects/validate_form`, customFormFile));
    }
  }, [customFormFile]);

  return (
    <CoreModules.Stack
      sx={{
        width: { xs: '100%', md: '80%' },
        justifyContent: 'space-between',
        gap: '4rem',
        marginLeft: { md: '215px !important' },
        pr: 2,
      }}
    >
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <Grid
            container
            spacing={{ xs: 2, md: 10 }}
            sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}
          >
            <Grid item xs={16} md={4} sx={{ display: 'flex', flexDirection: 'column' }}>
              <CoreModules.FormControl sx={{ mb: 3 }}>
                <InputLabel
                  id="form-category"
                  sx={{
                    '&.Mui-focused': {
                      color: defaultTheme.palette.black,
                    },
                  }}
                >
                  Form Selection
                </InputLabel>
                <Select
                  labelId="form_ways-label"
                  id="form_ways"
                  value={values.form_ways}
                  label="Form Selection"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('form_ways', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        form_ways: e.target.value,
                      }),
                    );
                  }}
                  // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'form_ways', value: e.target.value }))}
                >
                  {selectFormWays?.map((form) => (
                    <MenuItem key={form.value} value={form.value}>
                      {form.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.form_ways && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.form_ways}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl>

              {values.form_ways === 'Upload a Custom Form' ? (
                <>
                  <a download>
                    Download Form Template{' '}
                    <CoreModules.IconButton style={{ borderRadius: 0 }} color="primary" component="label">
                      <AssetModules.FileDownloadIcon style={{ color: '#2DCB70' }} />
                    </CoreModules.IconButton>
                  </a>
                  <CoreModules.FormLabel>Upload .xls/.xlsx/.xml Form</CoreModules.FormLabel>
                  <CoreModules.Button variant="contained" component="label">
                    <CoreModules.Input
                      type="file"
                      value={customFormInputValue}
                      onChange={(e) => {
                        setCustomFormFile(e.target.files[0]);
                      }}
                      inputProps={{ accept: '.xml, .xls, .xlsx' }}
                    />
                    <CoreModules.Typography component="h4">{customFormFile?.name}</CoreModules.Typography>
                  </CoreModules.Button>
                  {!values.uploaded_form && (
                    <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
                      Form File is required.
                    </CoreModules.FormLabel>
                  )}
                </>
              ) : null}
            </Grid>
            <Grid item md={8}>
              <CoreModules.Stack>
                {generateProjectLog ? (
                  <CoreModules.Stack
                    sx={{ display: 'flex', flexDirection: 'col', gap: 2, width: { xs: '100%', md: '60%' }, pb: '2rem' }}
                  >
                    <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
                      <CoreModules.Typography component="h4">Status: </CoreModules.Typography>
                      <CoreModules.Typography
                        component="h4"
                        sx={{ ml: 2, fontWeight: 'bold', borderRadius: '20px', border: '1px solid gray', p: 1 }}
                      >
                        {generateProjectLog.status}
                      </CoreModules.Typography>
                    </CoreModules.Stack>
                    <LoadingBar
                      title={'Task Progress'}
                      activeStep={generateProjectLog.progress}
                      totalSteps={totalSteps}
                    />
                  </CoreModules.Stack>
                ) : null}
                {generateProjectLog ? (
                  <CoreModules.Stack sx={{ width: '90%', height: '48vh' }}>
                    <div
                      ref={divRef}
                      style={{
                        backgroundColor: 'black',
                        color: 'white',
                        padding: '10px',
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        overflow: 'auto',
                        height: '100%',
                      }}
                    >
                      {renderTraceback(generateProjectLog?.logs)}
                    </div>
                  </CoreModules.Stack>
                ) : null}
              </CoreModules.Stack>
            </Grid>
          </Grid>
          <CoreModules.Stack
            sx={{
              display: 'flex',
              flexDirection: 'row',
              width: '100%',
              paddingRight: '5rem',
              gap: '12%',
            }}
          >
            {/* Previous Button  */}
            <Link to="/define-tasks">
              <CoreModules.Button sx={{ px: '20px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            {/* Submit Button For Create Project on Area Upload */}
            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <CoreModules.LoadingButton
                disabled={projectDetailsLoading}
                type="submit"
                loading={projectDetailsLoading}
                loadingPosition="end"
                endIcon={<AssetModules.SettingsSuggestIcon />}
                variant="contained"
                color="error"
              >
                Submit
              </CoreModules.LoadingButton>
            </CoreModules.Stack>
            {/* END */}
          </CoreModules.Stack>
        </FormGroup>
      </form>
    </CoreModules.Stack>
  );
};
export default FormSelection;
