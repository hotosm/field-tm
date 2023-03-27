import React, { useEffect } from "react";
import windowDimention from "../../hooks/WindowDimension";
import enviroment from "../../environment";
import CoreModules from "../../shared/CoreModules";
import { CreateProjectService } from "../../api/CreateProjectService";
import { useNavigate } from 'react-router-dom';
import useForm from "../../hooks/useForm";
import CreateProjectValidation from "./CreateProjectValidation";
import { diffObject } from "../../utilfunctions/compareUtils";


const ProjectDetailsForm = () => {
    const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension
    const navigate = useNavigate();

    const dispatch = CoreModules.useDispatch()
    // //dispatch function to perform redux state mutation

    const projectDetails = CoreModules.useSelector((state) => state.createproject.projectDetails);
    // //we use use selector from redux to get all state of projectDetails from createProject slice

    const projectDetailsResponse = CoreModules.useSelector((state) => state.createproject.projectDetailsResponse);
    // //we use use selector from redux to get all state of projectDetailsResponse from createProject slice

    // // passing payloads for creating project from form
    const onCreateProjectSubmission = (values) => {
        dispatch(CreateProjectService(`${enviroment.baseApiUrl}/projects/create_project`,
            {
                "project_info": { ...values },
                "author": {
                    "username": values.username,
                    "id": values.id
                },
            }
        ));
    }
    // Might Need To Fix little after all backend PR merges  // 

    useEffect(() => {
        if (projectDetailsResponse !== null) {
            navigate('/upload-area');
        }

    }, [projectDetailsResponse])

    const submission = () => {
        // eslint-disable-next-line no-use-before-define
        submitForm();
    };

    //   errors
    const { handleChange, handleSubmit, handleCustomChange, values, errors } = useForm(
        projectDetails,
        submission,
        CreateProjectValidation,
    );
    const submitForm = () => {
        // const changedValues = diffObject(projectDetails, values);
        onCreateProjectSubmission(values);
    };
    const inputFormStyles = () => {
        return {
            style: {
                color: defaultTheme.palette.error.main,
                fontFamily: defaultTheme.typography.fontFamily,
                fontSize: defaultTheme.typography.fontSize
            } // or className: 'your-class'
        }
    }
    return (
        <CoreModules.Stack sx={{ width: '50%' }}>
            <form onSubmit={handleSubmit}>
                <CoreModules.FormGroup>
                    {/* User Id Form Input For Create Project  as Oauth is Not Working   "FIX ME" */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>User Id<CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel>
                        </CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="id"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.id}
                            onChange={(e) => { handleCustomChange('id', e.target.value); }}
                            helperText={errors.id}
                            FormHelperTextProps={inputFormStyles()}
                        />
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* User Name Form Input For Create Project  as Oauth is Not Working   "FIX ME" */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Username  <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="username"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.username}
                            onChange={(e) => {
                                handleCustomChange('username', e.target.value);
                            }}
                            helperText={errors.username}
                            FormHelperTextProps={inputFormStyles()}

                        />
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Project Name Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Project Name <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="project_name"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.name}
                            onChange={(e) => {
                                handleCustomChange('name', e.target.value);
                            }}
                            helperText={errors.name}
                            FormHelperTextProps={inputFormStyles()}

                        />
                        {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Short Description Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Short Description <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="short_description"
                            label=""
                            variant="filled"
                            value={values.short_description}
                            onChange={(e) => {
                                handleCustomChange('short_description', e.target.value);
                            }}
                            multiline
                            rows={4}
                            helperText={errors.short_description}
                            FormHelperTextProps={inputFormStyles()}
                        />
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Description Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Description <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="description"
                            label=""
                            variant="filled"
                            value={values.description}
                            onChange={(e) => { handleCustomChange('description', e.target.value); }}
                            multiline
                            rows={4}
                            helperText={errors.description}
                            FormHelperTextProps={inputFormStyles()}
                        />
                    </CoreModules.FormControl>
                    {/* END */}

                    <CoreModules.Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'flex-end' }}>
                        {/* Form Submission Button For Create Project */}
                        <CoreModules.Button
                            variant="contained"
                            color="error"
                            sx={{ width: '20%' }}
                            type="submit"
                        >
                            Next
                        </CoreModules.Button>
                        {/* END */}
                    </CoreModules.Box>
                </CoreModules.FormGroup>
            </form>
        </CoreModules.Stack>
    )
};
export default ProjectDetailsForm;
