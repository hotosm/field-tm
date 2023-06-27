import React from 'react';
import enviroment from '../../environment';
import CoreModules from '../../shared/CoreModules';
import FormGroup from '@mui/material/FormGroup';
import { GetDividedTaskFromGeojson } from '../../api/CreateProjectService';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { InputLabel, MenuItem, Select } from '@mui/material';
import DefineAreaMap from 'map/DefineAreaMap';
import useForm from '../../hooks/useForm';
import DefineTaskValidation from './validation/DefineTaskValidation';

// const DefineAreaMap = React.lazy(() => import('map/DefineAreaMap'));
// const DefineAreaMap = React.lazy(() => import('map/DefineAreaMap'));
const alogrithmList = [{id:1,value:'Divide on Square',label:'Divide on Square'}, {id:2,value:'Choose Area as Tasks',label:'Choose Area as Tasks'}];
const DefineTasks: React.FC = ({geojsonFile}) => {
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  // // const state:any = useSelector<any>(state=>state.project.projectData)
  // // console.log('state main :',state)

  // const { type } = windowDimention();
  // //get window dimension

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
  // //we use use-selector from redux to get all state of projectDetails from createProject slice

  const submission = () => {
    // const previousValues = location.state.values;
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
    dispatch(
      GetDividedTaskFromGeojson(`${enviroment.baseApiUrl}/projects/preview_tasks/`, {
        geojson: geojsonFile,
        dimension: formValues?.dimension,
      }),
    );
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
  const dividedTaskGeojson = CoreModules.useSelector((state) => state.createproject.dividedTaskGeojson);
  const parsedTaskGeojsonCount =
  dividedTaskGeojson?.features?.length || JSON?.parse(dividedTaskGeojson)?.features?.length;
  // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
  // const filteredAlgorithmListData = algorithmListData?.filter((algo) => parsedTaskGeojsonCount > 1 ? algo.label === 'Choose Area as Tasks' : algo);
  console.log(dividedTaskGeojson,'dividedTaskGeojson');
  const algorithmListData =alogrithmList;
  // const algorithmListData = alogrithmList.filter((algorithm)=> {
  //   console.log(dividedTaskGeojson?.features?.length,'dividedTaskGeojson?.features?.length');
    
  //   return parsedTaskGeojsonCount>1 ? algorithm.label === 'Choose Area as Tasks':algorithm;
  // });
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
                <MenuItem key={listData.id} value={listData.value}>{listData.label}</MenuItem>
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
                    min="10"
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
                    InputProps={{ inputProps: { min: 50 } }}
                    FormHelperTextProps={inputFormStyles()}
                  />
                  {errors.dimension && (
                    <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                      {errors.dimension}
                    </CoreModules.FormLabel>
                  )}
                </CoreModules.Stack>
                <CoreModules.Button variant="contained" color="error" onClick={generateTasksOnMap}>
                  Generate Tasks
                </CoreModules.Button>
              </CoreModules.Stack>
            </CoreModules.FormControl>
          )}
          {parsedTaskGeojsonCount ? (
            <CoreModules.Stack direction="row" alignItems="center" spacing={2}>
              <h2>Total Tasks:</h2>
              <h3>{parsedTaskGeojsonCount}</h3>
            </CoreModules.Stack>
          ) : null}
          {/* END */}

          {/* Submit Button For Create Project on Area Upload */}
          <CoreModules.Stack
            sx={{ display: 'flex', flexDirection: 'row', width: '100%', justifyContent: 'space-evenly', gap: '5rem' }}
          >
            {/* Previous Button  */}
            <Link to="/upload-area">
              <CoreModules.Button sx={{ width: '100px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <CoreModules.Button variant="contained" color="error" sx={{ width: '20%' }} type="submit">
                Next
              </CoreModules.Button>
            </CoreModules.Stack>
          </CoreModules.Stack>
          {/* END */}
        </FormGroup>
      </form>
      <DefineAreaMap uploadedGeojson={geojsonFile}/>
    </CoreModules.Stack>
  );
};
export default DefineTasks;
