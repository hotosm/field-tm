import React, { useState, useEffect, useRef } from "react";
import enviroment from "../../environment";
import CoreModules from "../../shared/CoreModules";
import FormControl from '@mui/material/FormControl'
import FormGroup from '@mui/material/FormGroup'
import { FormCategoryService, GenerateProjectLog, GetDividedTaskFromGeojson } from "../../api/CreateProjectService";
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { InputLabel, MenuItem, Select } from "@mui/material";
import { CommonActions } from "../../store/slices/CommonSlice";
import DefineAreaMap from "map/DefineAreaMap";

let generateProjectLogIntervalCb = null
// const DefineAreaMap = React.lazy(() => import('map/DefineAreaMap'));
// const DefineAreaMap = React.lazy(() => import('map/DefineAreaMap'));

const UploadArea: React.FC = () => {
    const [fileUpload, setFileUpload] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)

    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension

    const dispatch = CoreModules.useDispatch()
    // //dispatch function to perform redux state mutation

    const projectArea = CoreModules.useSelector((state: any) => state.createproject.projectArea);
    // //we use use-selector from redux to get all state of projectDetails from createProject slice

    // const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
    // // //we use use-selector from redux to get all state of formCategory from createProject slice

    const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
    // //we use use-selector from redux to get all state of projectDetails from createProject slice

    const projectDetailsResponse = CoreModules.useSelector((state: any) => state.createproject.projectDetailsResponse);
    // //we use use-selector from redux to get all state of projectDetails from createProject slice

    const userDetails: any = CoreModules.useSelector<any>((state) => state.login.loginToken);
    // //we use use-selector from redux to get all state of loginToken from login slice
    // const generateQrLoading: any = CoreModules.useSelector<any>((state) => state.createproject.generateQrLoading);
    // //we use use-selector from redux to get all state of loginToken from login slice
    const generateProjectLog: any = CoreModules.useSelector<any>((state) => state.createproject.generateProjectLog);
    // //we use use-selector from redux to get all state of loginToken from login slice
    const generateQrSuccess: any = CoreModules.useSelector<any>((state) => state.createproject.generateQrSuccess);
    // //we use use-selector from redux to get all state of loginToken from login slice


    // if projectarea is not null navigate to projectslist page and that is when user submits create project
    useEffect(() => {
        if (projectArea !== null) {
            // navigate('/');
            dispatch(CreateProjectActions.ClearCreateProjectFormData())

        }
        return () => {
            dispatch(CreateProjectActions.ClearCreateProjectFormData())
        }

    }, [projectArea])
    // END

    // Fetching form category list 
    useEffect(() => {
        dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`))
        return () => {
            clearInterval(generateProjectLogIntervalCb);
        }
    }, [])
    // END

    // Fetching form category list 
    useEffect(() => {
        if (generateQrSuccess) {
            if (generateProjectLogIntervalCb === null) {
                dispatch(GenerateProjectLog(`${enviroment.baseApiUrl}/projects/generate-log/`, { project_id: projectDetailsResponse?.id, uuid: generateQrSuccess.task_id }));
            }
        }

    }, [generateQrSuccess])
    useEffect(() => {
        if (generateProjectLog?.status === 'SUCCESS') {
            clearInterval(generateProjectLogIntervalCb);
            navigate('/');
            dispatch(
                CommonActions.SetSnackBar({
                    open: true,
                    message: 'QR Generation Completed.',
                    variant: "success",
                    duration: 2000,
                })
            );
        }
        if (generateQrSuccess && generateProjectLog?.status === 'PENDING') {
            if (generateProjectLogIntervalCb === null) {
                generateProjectLogIntervalCb = setInterval(() => {
                    dispatch(GenerateProjectLog(`${enviroment.baseApiUrl}/projects/generate-log/`, { project_id: projectDetailsResponse?.id, uuid: generateQrSuccess.task_id }))
                }, 2000)
            }
        }


    }, [generateQrSuccess, generateProjectLog])
    // END

    const algorithmListData = ['Divide on Square', 'Custom Multipolygon', 'Openstreet Map Extract'].map(
        item => ({ label: item, value: item })
    );
    const inputFormStyles = () => {
        return {
            style: {
                color: defaultTheme.palette.error.main,
                fontFamily: defaultTheme.typography.fontFamily,
                fontSize: defaultTheme.typography.fontSize
            } // or className: 'your-class'
        }
    }

    const values = location?.state?.values;
    console.log(values, 'values');
    // // passing payloads for creating project from form whenever user clicks submit on upload area passing previous project details form aswell
    const onCreateProjectSubmission = () => {
        const { values } = location.state;
        // dispatch(CreateProjectService(`${enviroment.baseApiUrl}/projects/create_project`,
        //     {
        //         "project_info": { ...values },
        //         "author": {
        //             "username": userDetails.username,
        //             "id": userDetails.id
        //         },
        //         "odk_central": {
        //             "odk_central_url": values.odk_central_url,
        //             "odk_central_user": values.odk_central_user,
        //             "odk_central_password": values.odk_central_password
        //         },
        //         // dont send xform_title if upload custom form is selected 
        //         "xform_title": projectDetails.form_ways === 'Upload a Form' ? null : projectDetails.xform_title,
        //         "dimension": projectDetails.dimension,
        //         "splitting_algorithm": projectDetails.splitting_algorithm,
        //         "organization": values.organization,
        //         "form_ways": projectDetails.form_ways,
        //         "uploaded_form": values.uploaded_form,
        //         "data_extractWays": values.data_extractWays === 'Polygon' ? true : false,
        //     }, fileUpload
        // ));
    }
    const renderTraceback = (errorText: string) => {
        if (!errorText) {
            return null;
        }

        return errorText.split("\n").map((line, index) => (
            <div key={index} style={{ display: "flex" }}>
                <span style={{ color: "gray", marginRight: "1em" }}>{index + 1}.</span>
                <span>{line}</span>
            </div>
        ));
    };
    const divRef = useRef(null);
    useEffect(() => {
        console.log(divRef?.current, 'current');
        if (!divRef?.current) return;
        const myDiv = divRef?.current;
        myDiv.scrollTop = myDiv?.scrollHeight;
    });
    const generateTasksOnMap = () => {
        dispatch(GetDividedTaskFromGeojson(`${enviroment.baseApiUrl}/projects/preview_tasks/`, { geojson: fileUpload?.[0], dimension: projectDetails?.dimension }))
    }

    return (
        <CoreModules.Stack sx={{ width: '80%', display: 'flex', flexDirection: 'row', justifyContent: 'space-between' }}>
            <form>
                <FormGroup >
                    {/* <CoreModules.FormLabel>Splitting Algorithm</CoreModules.FormLabel> */}
                    <CoreModules.FormControl sx={{ mb: 3, width: '100%' }} variant="filled">
                        <InputLabel id="demo-simple-select-label" sx={{
                            '&.Mui-focused': {
                                color: defaultTheme.palette.black
                            }
                        }} >Choose Splitting Algorithm</InputLabel>
                        <Select
                            labelId="splitting_algorithm-label"
                            id="splitting_algorithm"
                            value={projectDetails.splitting_algorithm}
                            label="Splitting Algorithm"
                            onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'splitting_algorithm', value: e.target.value }))} >
                            {algorithmListData?.map((listData) => <MenuItem value={listData.value}>{listData.label}</MenuItem>)}
                        </Select>
                    </CoreModules.FormControl>
                    {/* Form Geojson File Upload For Create Project */}
                    {['Divide on Square', 'Custom Multipolygon'].includes(projectDetails.splitting_algorithm) && <FormControl sx={{ mb: 3 }}>
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
                    </FormControl>}
                    {/* END */}
                    {projectDetails.splitting_algorithm === 'Divide on Square' && <CoreModules.FormControl sx={{ mb: 3, width: '100%' }}>
                        <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                            <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '50%' }}>
                                <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}><CoreModules.FormLabel component="h3">Dimension (in metre)</CoreModules.FormLabel><CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.Box>
                                <CoreModules.TextField
                                    id="dimension"
                                    label=""
                                    variant="filled"
                                    inputProps={{ sx: { padding: '8.5px 14px' } }}
                                    value={projectDetails.dimension}
                                    onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'dimension', value: e.target.value }))}
                                    // helperText={errors.username}
                                    FormHelperTextProps={inputFormStyles()}

                                />
                            </CoreModules.Stack>
                            <CoreModules.Button
                                variant="contained"
                                color="error"
                                onClick={generateTasksOnMap}
                            >
                                Generate Tasks on Map
                            </CoreModules.Button>
                        </CoreModules.Stack>
                    </CoreModules.FormControl>}
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
            {generateProjectLog ? <CoreModules.Stack sx={{ width: '60%', height: '68vh' }}>
                <div ref={divRef} style={{ backgroundColor: 'black', color: 'white', padding: '10px', fontSize: '12px', whiteSpace: 'pre-wrap', fontFamily: 'monospace', overflow: 'auto', height: '100%' }}>
                    {renderTraceback(generateProjectLog?.logs)}
                </div>
            </CoreModules.Stack> : null}
            <DefineAreaMap uploadedGeojson={fileUpload?.[0]} />
        </CoreModules.Stack >
    )
};
export default UploadArea;
