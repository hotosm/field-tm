import React, { useEffect } from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import FormGroup from '@mui/material/FormGroup';
import { FormCategoryService } from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { Grid, InputLabel, MenuItem, Select } from '@mui/material';
import useForm from '../../hooks/useForm';
//@ts-ignore
import DefineAreaMap from 'map/DefineAreaMap';
import DataExtractValidation from './validation/DataExtractValidation';

// import { SelectPicker } from 'rsuite';
let generateProjectLogIntervalCb: any = null;

const DataExtract: React.FC<any> = ({
  geojsonFile,
  setGeojsonFile,
  dataExtractFile,
  setDataExtractFile,
  setDataExtractFileValue,
  lineExtractFile,
  setLineExtractFile,
  setLineExtractFileValue,
}) => {
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const navigate = useNavigate();

  const dispatch = CoreModules.useAppDispatch();
  // //dispatch function to perform redux state mutation

  const formCategoryList = CoreModules.useAppSelector((state) => state.createproject.formCategoryList);
  // //we use use-selector from redux to get all state of formCategory from createProject slice

  const projectDetails = CoreModules.useAppSelector((state) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END
  const selectExtractWaysList = ['Centroid', 'Polygon'];
  const selectExtractWays = selectExtractWaysList.map((item) => ({ label: item, value: item }));
  const dataExtractOptionsList = ['Data Extract Ways', 'Upload Custom Data Extract'];
  const dataExtractOptions = dataExtractOptionsList.map((item) => ({ label: item, value: item }));
  const formCategoryData = formCategoryList.map((item) => ({ label: item.title, value: item.title }));
  // //we use use-selector from redux to get state of dividedTaskGeojson from createProject slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`));
  }, []);
  // END

  const submission = () => {
    // const previousValues = location.state.values;
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...values }));
    navigate('/define-tasks');
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

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    DataExtractValidation,
  );
  useEffect(() => {
    if (values.data_extract_options === 'Data Extract Ways') {
      setDataExtractFile(null);
      setDataExtractFileValue(null);
      setLineExtractFile(null);
      setLineExtractFileValue(null);
    }
  }, [values.data_extract_options]);

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
                    <MenuItem key={form.label} value={form.value}>
                      {form.label}
                    </MenuItem>
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
                  Choose Data Extract
                </InputLabel>
                <Select
                  labelId="data_extract_options-label"
                  id="data_extract_options"
                  value={values.data_extract_options}
                  label="Data Extract Category"
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={(e) => {
                    handleCustomChange('data_extract_options', e.target.value);
                    dispatch(
                      CreateProjectActions.SetIndividualProjectDetailsData({
                        ...projectDetails,
                        data_extract_options: e.target.value,
                      }),
                    );
                  }}
                >
                  {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                  {dataExtractOptions?.map((form) => (
                    <MenuItem key={form.label} value={form.value}>
                      {form.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.data_extract_options && (
                  <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                    {errors.data_extract_options}
                  </CoreModules.FormLabel>
                )}
              </CoreModules.FormControl>
              {/* Area Geojson File Upload For Create Project */}
              {values.data_extract_options === `Upload Custom Data Extract` && (
                <>
                  <CoreModules.FormControl sx={{ mb: 3, width: '100%' }} variant="outlined">
                    <CoreModules.FormLabel>Upload {values.xform_title} </CoreModules.FormLabel>
                    <CoreModules.Button variant="contained" component="label">
                      <CoreModules.Input
                        sx={{ color: 'white' }}
                        type="file"
                        value={setDataExtractFileValue}
                        onChange={(e) => {
                          setDataExtractFile(e.target.files[0]);
                          handleCustomChange('data_extractFile', e.target.files[0]);
                        }}
                      />
                      <CoreModules.Typography component="h4">{dataExtractFile?.name}</CoreModules.Typography>
                    </CoreModules.Button>
                    {errors.data_extractFile && (
                      <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                        {errors.data_extractFile}
                      </CoreModules.FormLabel>
                    )}
                  </CoreModules.FormControl>
                  <CoreModules.FormControl sx={{ mb: 3, width: '100%' }} variant="outlined">
                    <CoreModules.FormLabel>Upload Lines </CoreModules.FormLabel>
                    <CoreModules.Button variant="contained" component="label">
                      <CoreModules.Input
                        sx={{ color: 'white' }}
                        type="file"
                        value={setLineExtractFileValue}
                        onChange={(e) => {
                          setLineExtractFile(e.target.files[0]);
                          handleCustomChange('line_extractFile', e.target.files[0]);
                        }}
                      />
                      <CoreModules.Typography component="h4">{lineExtractFile?.name}</CoreModules.Typography>
                    </CoreModules.Button>
                    {errors.lineExtractFile && (
                      <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                        {errors.lineExtractFile}
                      </CoreModules.FormLabel>
                    )}
                  </CoreModules.FormControl>
                </>
              )}

              {values.data_extract_options === 'Data Extract Ways' && (
                <CoreModules.FormControl sx={{ mb: 3 }}>
                  <InputLabel
                    id="form-category"
                    sx={{
                      '&.Mui-focused': {
                        color: defaultTheme.palette.black,
                      },
                    }}
                  >
                    Data Extract Type
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
                      <MenuItem key={form.label} value={form.value}>
                        {form.label}
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.data_extractWays && (
                    <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                      {errors.data_extractWays}
                    </CoreModules.FormLabel>
                  )}
                </CoreModules.FormControl>
              )}
            </Grid>
            <Grid item md={8}>
              <CoreModules.Stack>
                <DefineAreaMap
                  uploadedGeojson={geojsonFile}
                  setGeojsonFile={setGeojsonFile}
                  uploadedDataExtractFile={dataExtractFile}
                  uploadedLineExtractFile={lineExtractFile}
                />
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
            <Link to="/upload-area">
              <CoreModules.Button sx={{ px: '20px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            {/* Submit Button For Create Project on Area Upload */}
            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <CoreModules.LoadingButton
                // disabled={projectDetailsLoading}
                type="submit"
                // loading={projectDetailsLoading}
                // loadingPosition="end"
                // endIcon={<AssetModules.SettingsSuggestIcon />}
                variant="contained"
                color="error"
              >
                Next
              </CoreModules.LoadingButton>
            </CoreModules.Stack>
            {/* END */}
          </CoreModules.Stack>
        </FormGroup>
      </form>
    </CoreModules.Stack>
  );
};
export default DataExtract;
