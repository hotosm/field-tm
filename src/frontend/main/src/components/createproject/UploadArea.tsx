import React, { useState, useEffect } from "react";
import windowDimention from "../../hooks/WindowDimension";
import enviroment from "../../environment";
import CoreModules from "../../shared/CoreModules";
import FormControl from '@mui/material/FormControl'
import FormGroup from '@mui/material/FormGroup'
import { CreateProjectService, FormCategoryService, UploadAreaService } from "../../api/CreateProjectService";
import { useNavigate, useLocation } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { SelectPicker } from 'rsuite';

const UploadArea = () => {
    const [fileUpload, setFileUpload] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)

    const searchableInnerStyle: any = {
        toolbar: {
            marginTop: '0.7%',
            width: 250,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        outlineBtn: {
            width: 250,
            marginTop: '0.7%',
            borderRadius: 7,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        outlineBtnXs: {
            width: '50%',
            borderRadius: 7,
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },
        toolbarXs: {
            width: '50%',
            fontFamily: defaultTheme.typography.h3.fontFamily,
            fontSize: defaultTheme.typography.h3.fontSize
        },

    }
    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension

    const dispatch = CoreModules.useDispatch()
    // //dispatch function to perform redux state mutation

    const projectArea = CoreModules.useSelector((state: any) => state.createproject.projectArea);
    // //we use use selector from redux to get all state of projectDetails from createProject slice

    const projectDetailsResponse = CoreModules.useSelector((state: any) => state.createproject.projectDetailsResponse);
    // //we use use selector from redux to get all state of projectDetails from createProject slice

    const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
    // //we use use selector from redux to get all state of formCategory from createProject slice

    const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
    // //we use use selector from redux to get all state of projectDetails from createProject slice

    // const { id: projectId } = projectDetailsResponse;

    // if projectarea is not null navigate to projectslist page and that is when user submits create project
    useEffect(() => {
        if (projectArea !== null) {
            navigate('/');
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
    }, [])
    // END

    const formCategoryData = formCategoryList.map(
        item => ({ label: item.title, value: item.title })
    );
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

    // // passing payloads for creating project from form
    const onCreateProjectSubmission = () => {
        const { values } = location.state;
        dispatch(CreateProjectService(`${enviroment.baseApiUrl}/projects/create_project`,
            {
                "project_info": { ...values },
                "author": {
                    "username": values.username,
                    "id": values.id
                },
                "xform_title": projectDetails.xform_title,
                "dimension": projectDetails.dimension,
                "splitting_algorithm": projectDetails.splitting_algorithm,
            }, fileUpload
        ));
    }
    return (
        <CoreModules.Stack>
            <FormGroup >
                <CoreModules.FormLabel>Form Category</CoreModules.FormLabel>
                <SelectPicker data={formCategoryData}
                    style={{
                        marginBottom: '6%',
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                        fontSize: defaultTheme.typography.h3.fontSize
                    }}
                    color='red'
                    searchable={false}
                    onChange={(value) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value }))} />
                <CoreModules.FormLabel>Splitting Algorithm</CoreModules.FormLabel>
                <SelectPicker data={algorithmListData}
                    style={{
                        marginBottom: '6%',
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                        fontSize: defaultTheme.typography.h3.fontSize
                    }}
                    color='red'
                    searchable={false}
                    onChange={(value) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'splitting_algorithm', value }))} />

                {/* Square Input For Create Project inorder to set the square dimension of tasks*/}
                {projectDetails.splitting_algorithm === 'Divide on Square' && <CoreModules.FormControl sx={{ mb: 3 }}>
                    <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Dimension <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
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
                </CoreModules.FormControl>}
                {/* END */}


                {/* Form Geojson File Upload For Create Project */}
                {['Divide on Square', 'Custom Multipolygon'].includes(projectDetails.splitting_algorithm) && < FormControl sx={{ mb: 3 }}>
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

                {/* Submit Button For Create Project on Area Upload */}
                <CoreModules.Button
                    variant="contained"
                    color="error"
                    // disabled={!fileUpload ? true : false}
                    onClick={() => {
                        onCreateProjectSubmission();
                    }}
                >
                    Submit
                </CoreModules.Button>
                {/* END */}
            </FormGroup>
        </CoreModules.Stack >
    )
};
export default UploadArea;
