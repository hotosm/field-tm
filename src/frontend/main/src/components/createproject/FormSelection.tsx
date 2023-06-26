import React, { useEffect, useRef } from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import FormGroup from '@mui/material/FormGroup';
import { CreateProjectService, FormCategoryService, GenerateProjectLog } from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { Grid, InputLabel, MenuItem, Select } from '@mui/material';
import AssetModules from '../../shared/AssetModules.js';
import useForm from '../../hooks/useForm';
import SelectFormValidation from './validation/SelectFormValidation';
import { CommonActions } from '../../store/slices/CommonSlice';
import LoadingBar from './LoadingBar';

// import { SelectPicker } from 'rsuite';
let generateProjectLogIntervalCb = null;

const FormSelection: React.FC = ({geojsonFile}) => {
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  const navigate = useNavigate();

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
  // //we use use-selector from redux to get all state of formCategory from createProject slice

  const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END
  const selectExtractWaysList = ['Centroid', 'Polygon'];
  const selectExtractWays = selectExtractWaysList.map((item) => ({ label: item, value: item }));
  const selectFormWaysList = ['Use Existing Form', 'Upload a Custom Form'];
  const selectFormWays = selectFormWaysList.map((item) => ({ label: item, value: item }));
  const formCategoryData = formCategoryList.map((item) => ({ label: item.title, value: item.title }));
  const userDetails: any = CoreModules.useSelector<any>((state) => state.login.loginToken);
  // //we use use-selector from redux to get all state of loginToken from login slice

  const generateProjectLog: any = CoreModules.useSelector<any>((state) => state.createproject.generateProjectLog);
  // //we use use-selector from redux to get all state of loginToken from login slice
  const generateQrSuccess: any = CoreModules.useSelector<any>((state) => state.createproject.generateQrSuccess);
  // //we use use-selector from redux to get all state of loginToken from login slice
  const projectDetailsResponse = CoreModules.useSelector((state: any) => state.createproject.projectDetailsResponse);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  const dividedTaskGeojson = CoreModules.useSelector((state) => state.createproject.dividedTaskGeojson);
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END

  const submission = () => {
    dispatch(
      CreateProjectService(
        `${enviroment.baseApiUrl}/projects/create_project`,
        {
          project_info: {
            name: projectDetails.name,
            short_description: projectDetails.short_description,
            description: projectDetails.description,
          },
          author: {
            username: userDetails.username,
            id: userDetails.id,
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
          organization: projectDetails.organization,
          form_ways: projectDetails.form_ways,
          // "uploaded_form": projectDetails.uploaded_form,
          data_extractWays: projectDetails.data_extractWays,
        },
        geojsonFile,
        values.uploaded_form?.[0],
      ),
    );
    // navigate("/select-form", { replace: true, state: { values: values } });
  };

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
    return () => {
      clearInterval(generateProjectLogIntervalCb);
      dispatch(CreateProjectActions.SetGenerateProjectLog(null));
    };
  }, []);
  // END

  // Fetching form category list
  useEffect(() => {
    if (generateQrSuccess) {
      if (generateProjectLogIntervalCb === null) {
        dispatch(
          GenerateProjectLog(`${enviroment.baseApiUrl}/projects/generate-log/`, {
            project_id: projectDetailsResponse?.id,
            uuid: generateQrSuccess.task_id,
          }),
        );
      }
    }
  }, [generateQrSuccess]);
  useEffect(() => {
    if (generateQrSuccess && generateProjectLog?.status === 'SUCCESS') {
      clearInterval(generateProjectLogIntervalCb);
      navigate('/');
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
            GenerateProjectLog(`${enviroment.baseApiUrl}/projects/generate-log/`, {
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
    const myDiv = divRef?.current;
    myDiv.scrollTop = myDiv?.scrollHeight;
  });

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    SelectFormValidation,
  );
  const parsedTaskGeojsonCount =
    dividedTaskGeojson?.features?.length || JSON?.parse(dividedTaskGeojson)?.features?.length || projectDetails?.areaGeojson?.features?.length;
  const totalSteps = dividedTaskGeojson?.features ? dividedTaskGeojson?.features?.length : parsedTaskGeojsonCount;

  return (
    <CoreModules.Stack
      sx={{
        width: { xs: '95%', md: '80%' },
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        justifyContent: 'space-between',
        gap: '4rem',
        marginLeft: { md: '215px !important' },
        pr: 2,
      }}
    >
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <Grid container spacing={5}>
            <Grid item xs={40} md={40} sx={{ display: 'flex', flexDirection: 'column' }}>
              <CoreModules.FormControl sx={{ mb: 3 }}>
                <InputLabel
                  id="form-category"
                  sx={{
                    '&.Mui-focused': {
                      color: defaultTheme.palette.black,
                    },
                  }}
                >
                  Data Extract Category
                </InputLabel>
                <Select
                  labelId="data_extractWays-label"
                  id="data_extractWays"
                  value={values.data_extractWays}
                  label="Data Extract Category"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('data_extractWays', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        data_extractWays: e.target.value,
                      }),
                    );
                  }}
                >
                  {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                  {selectExtractWays?.map((form) => (
                    <MenuItem value={form.value}>{form.label}</MenuItem>
                  ))}
                </Select>
                {errors.data_extractWays && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.data_extractWays}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl>
              <CoreModules.FormControl sx={{ mb: 3 }}>
                <InputLabel
                  id="form-category"
                  sx={{
                    '&.Mui-focused': {
                      color: defaultTheme.palette.black,
                    },
                  }}
                >
                  Form Category
                </InputLabel>
                <Select
                  labelId="form_category-label"
                  id="form_category"
                  value={values.xform_title}
                  label="Form Category"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('xform_title', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        xform_title: e.target.value,
                      }),
                    );
                  }}
                >
                  {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                  {formCategoryData?.map((form) => (
                    <MenuItem value={form.value}>{form.label}</MenuItem>
                  ))}
                </Select>
                {errors.xform_title && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.xform_title}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl>
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
                    <MenuItem value={form.value}>{form.label}</MenuItem>
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
                      onChange={(e) => {
                        handleCustomChange('uploaded_form', e.target.files);
                        dispatch(
                          CreateProjectActions.SetIndividualProjectDetailsData({
                            ...projectDetails,
                            uploaded_form: e.target.files[0],
                            uploadedFormFileName: e.target.files[0].name,
                          }),
                        );

                        // setFormFileUpload(e.target.files)
                      }}
                    />
                  </CoreModules.Button>
                  {!values.uploaded_form && (
                    <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
                      Form File is required.
                    </CoreModules.FormLabel>
                  )}
                </>
              ) : null}
            </Grid>
            <Grid item xs={8}>
              <CoreModules.Stack>
                {generateProjectLog ? (
                  <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'col', gap: 2, width: '60%', pb: '2rem' }}>
                    <LoadingBar
                      title={'Task Progress'}
                      // steps={totalSteps}
                      // activeStep={10}
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
              <CoreModules.Button
                sx={{ px: '20px' }}
                variant="contained"
                color="error"
                type="submit"
              // disabled={!fileUpload ? true : false}
              >
                Submit
              </CoreModules.Button>
            </CoreModules.Stack>
            {/* END */}
          </CoreModules.Stack>
        </FormGroup>
      </form>
    </CoreModules.Stack>
  );
};
export default FormSelection;
