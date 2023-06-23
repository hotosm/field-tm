import React, { useEffect, useState } from 'react';
import CoreModules from '../../shared/CoreModules';
import FormControl from '@mui/material/FormControl';
import FormGroup from '@mui/material/FormGroup';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import DefineAreaMap from 'map/DefineAreaMap';

const UploadArea: React.FC = () => {
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  const projectDetails: any = CoreModules.useSelector<any>((state) => state.createproject.projectDetails);
  // //we use use selector from redux to get all state of projectDetails from createProject slice

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  // if projectarea is not null navigate to projectslist page and that is when user submits create project
  // useEffect(() => {
  //     if (projectArea !== null) {
  //         // navigate('/');
  //         dispatch(CreateProjectActions.ClearCreateProjectFormData())

  //     }
  //     return () => {
  //         dispatch(CreateProjectActions.ClearCreateProjectFormData())
  //     }

  // }, [projectArea])
  // // END

  // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
  const onCreateProjectSubmission = () => {
    if (!projectDetails.areaGeojson) return;
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
                type="file"
                // value={projectDetails.areaGeojsonfileName || ''}
                onChange={(e) => {
                  dispatch(
                    CreateProjectActions.SetIndividualProjectDetailsData({
                      ...projectDetails,
                      areaGeojson: e.target.files[0],
                      areaGeojsonfileName: e.target.files[0].name,
                    }),
                  );
                }}
              />
              {/* <CoreModules.Typography component="h4">{projectDetails?.areaGeojsonfileName}</CoreModules.Typography> */}
            </CoreModules.Button>
            {!projectDetails.areaGeojson && (
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
      <DefineAreaMap uploadedGeojson={projectDetails?.areaGeojson} />
    </CoreModules.Stack>
  );
};
export default UploadArea;
