import React, { useState } from "react";
import CoreModules from "../../shared/CoreModules";
import FormControl from '@mui/material/FormControl'
import FormGroup from '@mui/material/FormGroup'
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import DefineAreaMap from "map/DefineAreaMap";

const UploadArea: React.FC = () => {
    const [fileUpload, setFileUpload] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)


    const dispatch = CoreModules.useDispatch()
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




    const values = location?.state?.values;
    console.log(values, 'values');
    // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
    const onCreateProjectSubmission = () => {
        if (!fileUpload) return;
        const { values } = location.state;
        dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...values }));
        dispatch(CreateProjectActions.SetCreateProjectFormStep('select-form'));
        navigate("/define-tasks", { replace: true, state: { values: { ...values, areaGeojson: fileUpload?.[0] } } });
    }


    return (
        <CoreModules.Stack sx={{ width: '80%', display: 'flex', flexDirection: 'row', justifyContent: 'space-between' }}>
            <form>
                <FormGroup >
                    {/* Area Geojson File Upload For Create Project */}
                    <FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel>Upload GEOJSON</CoreModules.FormLabel>
                        <CoreModules.Button
                            variant="contained"
                            component="label"
                        >
                            <CoreModules.Input
                                type="file"
                                onChange={(e) => {
                                    setFileUpload(e.target.files)
                                }}
                            />
                        </CoreModules.Button>
                        {!fileUpload && <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>Geojson file is required.</CoreModules.FormLabel>}
                    </FormControl>
                    {/* END */}



                    {/* Submit Button For Create Project on Area Upload */}
                    <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', width: '100%', justifyContent: 'space-between' }}>
                        {/* Previous Button  */}
                        <Link to="/select-form">
                            <CoreModules.Button
                                sx={{ width: '150px' }}
                                variant="outlined"
                                color="error"
                            >
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
            <DefineAreaMap uploadedGeojson={fileUpload?.[0]} />
        </CoreModules.Stack >
    )
};
export default UploadArea;
