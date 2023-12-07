import React from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules.js';
import FormGroup from '@mui/material/FormGroup';
import { GetDividedTaskFromGeojson, TaskSplittingPreviewService } from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { InputLabel, MenuItem, Select } from '@mui/material';
//@ts-ignore
import DefineAreaMap from '../../views/DefineAreaMap';
import useForm from '../../hooks/useForm';
import DefineTaskValidation from './validation/DefineTaskValidation';
import { useAppSelector } from '../../types/reduxTypes';

const alogrithmList = [
  { id: 1, value: 'Divide on Square', label: 'Divide on Square' },
  { id: 2, value: 'Choose Area as Tasks', label: 'Choose Area as Tasks' },
  { id: 3, value: 'Task Splitting Algorithm', label: 'Task Splitting Algorithm' },
];
const DefineTasks: React.FC<any> = ({ geojsonFile, setGeojsonFile, dataExtractFile }) => {
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const drawnGeojson = CoreModules.useAppSelector((state) => state.createproject.drawnGeojson);

  // // const state:any = CoreModules.useAppSelector(state=>state.project.projectData)
  // // console.log('state main :',state)

  // const { type } = windowDimention();
  // //get window dimension

  const dispatch = CoreModules.useAppDispatch();
  // //dispatch function to perform redux state mutation

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  const submission = () => {
    // const previousValues = location.state.values;
    if (formValues.splitting_algorithm === 'Divide on Square') {
      generateTasksOnMap();
    }
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...formValues }));
    navigate('/select-form');
  };

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DefineTaskValidation);

  const generateTasksOnMap = () => {
    if (drawnGeojson) {
      const drawnGeojsonString = JSON.stringify(drawnGeojson, null, 2);

      const blob = new Blob([drawnGeojsonString], { type: 'application/json' });

      // Create a file object from the Blob
      const drawnGeojsonFile = new File([blob], 'data.json', { type: 'application/json' });
      dispatch(
        GetDividedTaskFromGeojson(`${import.meta.env.VITE_API_URL}/projects/preview_split_by_square/`, {
          geojson: drawnGeojsonFile,
          dimension: formValues?.dimension,
        }),
      );
    } else {
      dispatch(
        GetDividedTaskFromGeojson(`${import.meta.env.VITE_API_URL}/projects/preview_split_by_square/`, {
          geojson: geojsonFile,
          dimension: formValues?.dimension,
        }),
      );
    }
  };

  const generateTaskWithSplittingAlgorithm = () => {
    if (drawnGeojson) {
      const drawnGeojsonString = JSON.stringify(drawnGeojson, null, 2);

      const blob = new Blob([drawnGeojsonString], { type: 'application/json' });

      // Create a file object from the Blob
      const drawnGeojsonFile = new File([blob], 'data.json', { type: 'application/json' });
      dispatch(
        TaskSplittingPreviewService(
          `${import.meta.env.VITE_API_URL}/projects/task_split`,
          drawnGeojsonFile,
          formValues?.no_of_buildings,
          dataExtractFile,
        ),
      );
    } else {
      dispatch(
        TaskSplittingPreviewService(
          `${import.meta.env.VITE_API_URL}/projects/task_split`,
          geojsonFile,
          formValues?.no_of_buildings,
          dataExtractFile,
        ),
      );
    }
  };

  // 'Use natural Boundary'
  const inputFormStyles = () => {
    return {
      style: {
        color: defaultTheme.palette.error.main,
        fontFamily: defaultTheme.typography.fontFamily,
        fontSize: defaultTheme.typography.fontSize,
      }, // or className: 'your-class'
    };
  };
  const dividedTaskGeojson = CoreModules.useAppSelector((state) => state.createproject.dividedTaskGeojson);
  const parsedTaskGeojsonCount = dividedTaskGeojson?.features?.length || 1;
  // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
  const algorithmListData = alogrithmList;
  const dividedTaskLoading = CoreModules.useAppSelector((state) => state.createproject.dividedTaskLoading);
  const taskSplittingGeojsonLoading = CoreModules.useAppSelector(
    (state) => state.createproject.taskSplittingGeojsonLoading,
  );

  return (
    <CoreModules.Stack
      sx={{
        width: { xs: '95%', md: '80%' },
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        justifyContent: 'space-between',
        gap: '4rem',
        marginLeft: { md: '215px !important' },
        px: 2,
      }}
    >
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <CoreModules.FormControl sx={{ mb: 3, width: '100%' }}>
            <InputLabel
              id="demo-simple-select-label"
              sx={{
                '&.Mui-focused': {
                  color: defaultTheme.palette.black,
                },
              }}
            >
              Choose Splitting Algorithm
            </InputLabel>
            <Select
              labelId="splitting_algorithm-label"
              id="splitting_algorithm"
              value={formValues.splitting_algorithm}
              label="Choose Splitting Algorithm"
              // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'splitting_algorithm', value: e.target.value }))} >
              sx={{
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  border: '2px solid black',
                },
              }}
              onChange={(e) => {
                handleCustomChange('splitting_algorithm', e.target.value);
              }}
            >
              {algorithmListData?.map((listData) => (
                <MenuItem key={listData.id} value={listData.value}>
                  {listData.label}
                </MenuItem>
              ))}
            </Select>
            {errors.splitting_algorithm && (
              <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                {errors.splitting_algorithm}
              </CoreModules.FormLabel>
            )}
          </CoreModules.FormControl>
          {formValues.splitting_algorithm === 'Divide on Square' && (
            <CoreModules.FormControl sx={{ mb: 3, width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel component="h3">Dimension (in metre)</CoreModules.FormLabel>
                <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                  *
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.Stack
                sx={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '20px',
                }}
              >
                <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '50%' }}>
                  <CoreModules.TextField
                    id="dimension"
                    label=""
                    type="number"
                    min="9"
                    inputProps={{ sx: { padding: '8.5px 14px' } }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '&.Mui-focused fieldset': {
                          borderColor: 'black',
                        },
                      },
                    }}
                    value={formValues.dimension}
                    onChange={(e) => {
                      handleCustomChange('dimension', e.target.value);
                    }}
                    // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'dimension', value: e.target.value }))}
                    // helperText={errors.username}
                    InputProps={{ inputProps: { min: 9 } }}
                    FormHelperTextProps={inputFormStyles()}
                  />
                  {errors.dimension && (
                    <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                      {errors.dimension}
                    </CoreModules.FormLabel>
                  )}
                </CoreModules.Stack>
                <CoreModules.LoadingButton
                  disabled={formValues?.dimension < 10}
                  onClick={generateTasksOnMap}
                  loading={dividedTaskLoading}
                  loadingPosition="end"
                  endIcon={<AssetModules.SettingsSuggestIcon />}
                  variant="contained"
                  color="error"
                >
                  Generate Tasks
                </CoreModules.LoadingButton>
              </CoreModules.Stack>
            </CoreModules.FormControl>
          )}
          {formValues.splitting_algorithm === 'Task Splitting Algorithm' ? (
            <>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel component="h3">Average No. of Building in Task</CoreModules.FormLabel>
                <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                  *
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.Stack
                sx={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '20px',
                }}
              >
                <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '50%' }}>
                  <CoreModules.TextField
                    id="no_of_buildings"
                    disabled={taskSplittingGeojsonLoading}
                    label=""
                    type="number"
                    min="5"
                    inputProps={{ sx: { padding: '8.5px 14px' } }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '&.Mui-focused fieldset': {
                          borderColor: 'black',
                        },
                      },
                    }}
                    value={formValues.no_of_buildings}
                    onChange={(e) => {
                      handleCustomChange('no_of_buildings', e.target.value);
                    }}
                    // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'no_of_buildings', value: e.target.value }))}
                    // helperText={errors.username}
                    InputProps={{ inputProps: { min: 5 } }}
                    FormHelperTextProps={inputFormStyles()}
                  />
                  {errors.no_of_buildings && (
                    <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                      {errors.no_of_buildings}
                    </CoreModules.FormLabel>
                  )}
                </CoreModules.Stack>
                <CoreModules.LoadingButton
                  sx={{ mb: 3 }}
                  // disabled={formValues?.no_of_buildings < 10}
                  onClick={generateTaskWithSplittingAlgorithm}
                  loading={taskSplittingGeojsonLoading}
                  loadingPosition="end"
                  endIcon={<AssetModules.SettingsSuggestIcon />}
                  variant="contained"
                  color="error"
                >
                  Generate Tasks
                </CoreModules.LoadingButton>
              </CoreModules.Stack>
            </>
          ) : null}

          {parsedTaskGeojsonCount ? (
            <CoreModules.Stack direction="row" alignItems="center" spacing={2}>
              <h2>Total Tasks:</h2>
              <h3>{parsedTaskGeojsonCount}</h3>
            </CoreModules.Stack>
          ) : null}
          {/* END */}

          {/* Submit Button For Create Project on Area Upload */}
          <CoreModules.Stack
            sx={{
              display: 'flex',
              flexDirection: 'row',
              width: '100%',
              justifyContent: 'space-evenly',
              gap: '5rem',
              mt: 6,
            }}
          >
            {/* Previous Button  */}
            <Link to="/data-extract">
              <CoreModules.Button sx={{ width: '100px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <CoreModules.Button
                disabled={!dividedTaskGeojson}
                variant="contained"
                color="error"
                sx={{ width: '20%' }}
                type="submit"
              >
                Next
              </CoreModules.Button>
            </CoreModules.Stack>
          </CoreModules.Stack>
          {/* END */}
        </FormGroup>
      </form>
      <DefineAreaMap
        uploadedGeojson={geojsonFile}
        setGeojsonFile={setGeojsonFile}
        uploadedDataExtractFile={dataExtractFile}
      />
    </CoreModules.Stack>
  );
};
export default DefineTasks;
