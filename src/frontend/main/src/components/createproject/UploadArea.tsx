import React, { useEffect, useState } from 'react';
import CoreModules from '../../shared/CoreModules';
import FormControl from '@mui/material/FormControl';
import FormGroup from '@mui/material/FormGroup';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import DefineAreaMap from 'map/DefineAreaMap';

const UploadArea: React.FC = ({geojsonFile,setGeojsonFile,setInputValue,inputValue}) => {
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  const projectDetails: any = CoreModules.useSelector<any>((state) => state.createproject.projectDetails);
  // //we use use selector from redux to get all state of projectDetails from createProject slice

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation


  // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
  const onCreateProjectSubmission = () => {
    if (!geojsonFile) return;
    // dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, areaGeojson: fileUpload?.[0], areaGeojsonfileName: fileUpload?.name }));
    dispatch(CreateProjectActions.SetCreateProjectFormStep('select-form'));
    navigate('/define-tasks');
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
          <FormControl sx={{ mb: 3, width: '100%' }} variant="outlined">
            <CoreModules.FormLabel>Upload GEOJSON</CoreModules.FormLabel>
            <CoreModules.Button variant="contained" component="label">
              <CoreModules.Input
                sx={{color:'white'}}
                type="file"
                value={inputValue}
                onChange={(e) => {
                  setGeojsonFile(e.target.files[0]);
                }}
              />
              <CoreModules.Typography component="h4">{geojsonFile?.name}</CoreModules.Typography>
            </CoreModules.Button>
            {!geojsonFile && (
              <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
                Geojson file is required.
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
            {/* <CustomizedModal isOpen={openTerminal} toggleOpen={setOpenTerminal}>
                            
                        </CustomizedModal> */}
          </CoreModules.Stack>
          {/* END */}
        </FormGroup>
      </form>
      <DefineAreaMap uploadedGeojson={geojsonFile} />
    </CoreModules.Stack>
  );
};
export default UploadArea;
