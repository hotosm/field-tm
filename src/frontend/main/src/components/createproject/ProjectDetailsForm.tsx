import React, { useEffect } from "react";
import windowDimention from "../../hooks/WindowDimension";
import CoreModules from "../../shared/CoreModules";
import { useNavigate } from 'react-router-dom';
import useForm from "../../hooks/useForm";
import CreateProjectValidation from "./CreateProjectValidation";
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { SelectPicker } from 'rsuite';


const ProjectDetailsForm: React.FC = () => {
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


    useEffect(() => {
        if (projectDetailsResponse !== null) {
            navigate('/upload-area');
        }

    }, [projectDetailsResponse])

    const submission = () => {
        // eslint-disable-next-line no-use-before-define
        // submitForm();
        dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
        navigate("/upload-area", { replace: true, state: { values: values } });


    };

    const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
        projectDetails,
        submission,
        CreateProjectValidation,
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
    const organizationList = ['Naxa', 'Org 1', 'Org 2'].map(
        item => ({ label: item, value: item })
    );
    return (
        <CoreModules.Stack sx={{ width: '50%' }}>
            <form onSubmit={handleSubmit}>
                <CoreModules.FormGroup>
                    {/* Organization Dropdown For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Organization<CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <SelectPicker data={organizationList}
                            style={{
                                width: '40%',
                                fontFamily: defaultTheme.typography.h3.fontFamily,
                                fontSize: defaultTheme.typography.h3.fontSize
                            }}

                            searchable={false}
                            onChange={(value) => {
                                handleCustomChange('organization', value);
                                dispatch(CreateProjectActions.SetProjectDetails({ key: 'organization', value }))
                            }
                            } />
                        {errors.organization && <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>{errors.organization}</CoreModules.FormLabel>}
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Project Name Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Central ODK Url<CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="odk_central_url"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.odk_central_url}
                            onChange={(e) => {
                                handleCustomChange('odk_central_url', e.target.value);
                            }}
                            helperText={errors.odk_central_url}
                            FormHelperTextProps={inputFormStyles()}

                        />
                        {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Project Name Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Central ODK Email/Username <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="odk_central_user"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.odk_central_user}
                            onChange={(e) => {
                                handleCustomChange('odk_central_user', e.target.value);
                            }}
                            helperText={errors.odk_central_user}
                            FormHelperTextProps={inputFormStyles()}

                        />
                        {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
                    </CoreModules.FormControl>
                    {/* END */}

                    {/* Project Name Form Input For Create Project */}
                    <CoreModules.FormControl sx={{ mb: 3 }}>
                        <CoreModules.FormLabel component="h3" sx={{ display: 'flex' }}>Central ODK Password <CoreModules.FormLabel component="h4" sx={{ color: 'red' }}>*</CoreModules.FormLabel></CoreModules.FormLabel>
                        <CoreModules.TextField
                            id="odk_central_password"
                            label=""
                            variant="filled"
                            inputProps={{ sx: { padding: '8.5px 14px' } }}
                            value={values.odk_central_password}
                            onChange={(e) => {
                                handleCustomChange('odk_central_password', e.target.value);
                            }}
                            helperText={errors.odk_central_password}
                            FormHelperTextProps={inputFormStyles()}

                        />
                        {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
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
