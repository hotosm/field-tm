import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import FormControl from '@mui/material/FormControl';
import FormGroup from '@mui/material/FormGroup';
import { useNavigate, Link } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import DrawSvg from '@/components/createproject/DrawSvg';
// @ts-ignore
const DefineAreaMap = React.lazy(() => import('../../views/DefineAreaMap'));

const UploadArea: React.FC<any> = ({ geojsonFile, setGeojsonFile, setInputValue, inputValue }: any) => {
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const drawToggle = CoreModules.useAppSelector((state) => state.createproject.drawToggle);
  const drawnGeojson = CoreModules.useAppSelector((state) => state.createproject.drawnGeojson);
  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation

  useEffect(() => {
    dispatch(CreateProjectActions.SetDrawToggle(false));
  }, []);

  // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
  const onCreateProjectSubmission = () => {
    console.log(drawnGeojson, 'drawnGeojson');
    console.log(geojsonFile, 'geojsonFile');

    if (drawnGeojson) {
      dispatch(CreateProjectActions.SetCreateProjectFormStep('select-form'));
      navigate('/data-extract');
    } else if (!drawnGeojson && !geojsonFile) {
      return;
    } else {
      dispatch(CreateProjectActions.SetCreateProjectFormStep('select-form'));
      navigate('/data-extract');
    }
    // dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, areaGeojson: fileUpload?.[0], areaGeojsonfileName: fileUpload?.name }));
  };

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
      {/* <CoreModules.Stack sx={{ width: { xs: '95%' }, marginLeft: { md: '215px !important' } }}> */}
      <form>
        <FormGroup>
          {/* Area Geojson File Upload For Create Project */}
          <FormControl sx={{ mb: 3 }} variant="outlined">
            <CoreModules.Button
              variant="contained"
              sx={{ fontSize: '13px', background: drawToggle ? defaultTheme.palette.primary.lightblue : 'white' }}
              onClick={() => {
                dispatch(CreateProjectActions.SetDrawToggle(!drawToggle));
              }}
            >
              <DrawSvg />
              Draw
            </CoreModules.Button>
          </FormControl>
          <CoreModules.FormLabel sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>OR</CoreModules.FormLabel>

          <FormControl sx={{ mb: 3, width: '100%' }} variant="outlined">
            <CoreModules.FormLabel>Upload GEOJSON</CoreModules.FormLabel>
            <CoreModules.Button variant="contained" component="label">
              <CoreModules.Input
                sx={{ color: 'white' }}
                type="file"
                value={inputValue}
                onChange={(e) => {
                  dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
                  setGeojsonFile(e.target.files[0]);
                }}
                inputProps={{ accept: '.geojson, .json' }}
              />
              <CoreModules.Typography component="h4">{geojsonFile?.name}</CoreModules.Typography>
            </CoreModules.Button>
            {!drawnGeojson && !geojsonFile && (
              <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
                Draw an AOI Or Upload a Geojson file.
              </CoreModules.FormLabel>
            )}
          </FormControl>
          {/* END */}

          {/* Submit Button For Create Project on Area Upload */}
          <CoreModules.Stack
            sx={{ display: 'flex', flexDirection: 'row', width: '100%', justifyContent: 'space-evenly' }}
          >
            {/* Previous Button  */}
            <Link to="/create-project">
              <CoreModules.Button sx={{ width: '100px' }} variant="outlined" color="error">
                Previous
              </CoreModules.Button>
            </Link>
            {/* END */}

            <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <CoreModules.Button
                variant="contained"
                color="error"
                sx={{ width: '20%' }}
                // disabled={!fileUpload ? true : false}
                onClick={() => {
                  onCreateProjectSubmission();
                }}
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
        onDraw={(geojson) => {
          // dispatch(CreateProjectActions.SetDividedTaskGeojson(JSON.parse(geojson)));
          dispatch(CreateProjectActions.SetDrawnGeojson(JSON.parse(geojson)));
          // setGeojsonFile(JSON.parse(geojson));
        }}
      />
    </CoreModules.Stack>
  );
};
export default UploadArea;
