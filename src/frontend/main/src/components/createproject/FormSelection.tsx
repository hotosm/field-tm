import React, { useState, useEffect } from "react";
import windowDimention from "../../hooks/WindowDimension";
import enviroment from "../../environment";
import CoreModules from "../../shared/CoreModules";
import FormControl from '@mui/material/FormControl'
import FormGroup from '@mui/material/FormGroup'
import { CreateProjectService, FormCategoryService } from "../../api/CreateProjectService";
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { InputLabel, MenuItem, Select } from "@mui/material";
import AssetModules from '../../shared/AssetModules.js';
import useForm from "../../hooks/useForm";
import SelectFormValidation from "./validation/SelectFormValidation";

// import { SelectPicker } from 'rsuite';

const FormSelection: React.FC = () => {
    const [formFileUpload, setFormFileUpload] = useState(null);
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)
    const navigate = useNavigate();

    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension

    const dispatch = CoreModules.useDispatch()
    // //dispatch function to perform redux state mutation


    const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
    // //we use use-selector from redux to get all state of formCategory from createProject slice

    const projectDetails = CoreModules.useSelector((state: any) => state.createproject.projectDetails);
    // //we use use-selector from redux to get all state of projectDetails from createProject slice


    // Fetching form category list 
    useEffect(() => {
        dispatch(FormCategoryService(`${enviroment.baseApiUrl}/central/list-forms`))
    }, [])
    // END
    const selectFormWaysList = ['Use Existing Form', 'Upload a Custom Form'];
    const selectFormWays = selectFormWaysList.map(
        item => ({ label: item, value: item })
    );
    const formCategoryData = formCategoryList.map(
        item => ({ label: item.title, value: item.title })
    );

    const submission = () => {
        // eslint-disable-next-line no-use-before-define
        // submitForm();
        dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
        dispatch(CreateProjectActions.SetCreateProjectFormStep('upload-area'));
        navigate("/upload-area", { replace: true, state: { values: values } });


    };

    const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
        projectDetails,
        submission,
        SelectFormValidation,
    );
    console.log(values, 'values');
    console.log(errors, 'errors');
    return (
        <CoreModules.Stack sx={{ width: '50%' }}>
            <form onSubmit={handleSubmit}>
                <FormGroup >
                    <CoreModules.FormControl sx={{ mb: 3, width: '30%' }} variant="filled">
                        <InputLabel id="form-category" sx={{
                            '&.Mui-focused': {
                                color: defaultTheme.palette.black
                            }
                        }} >Form Category</InputLabel>
                        <Select
                            labelId="form_category-label"
                            id="form_category"
                            value={values.xform_title}
                            label="Form Category"
                            onChange={(e) => handleCustomChange('xform_title', e.target.value)}
                        >
                            {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
                            {formCategoryData?.map((form) => <MenuItem value={form.value}>{form.label}</MenuItem>)}
                        </Select>
                        {errors.xform_title && <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>{errors.xform_title}</CoreModules.FormLabel>}
                    </CoreModules.FormControl>
                    <CoreModules.FormControl sx={{ mb: 3, width: '30%' }} variant="filled">
                        <InputLabel id="form-category" sx={{
                            '&.Mui-focused': {
                                color: defaultTheme.palette.black
                            }
                        }}>Form Selection</InputLabel>
                        <Select
                            labelId="form_ways-label"
                            id="form_ways"
                            value={values.form_ways}
                            label="Form Ways"
                            onChange={(e) => handleCustomChange('form_ways', e.target.value)}
                        // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'form_ways', value: e.target.value }))} 
                        >
                            {selectFormWays?.map((form) => <MenuItem value={form.value}>{form.label}</MenuItem>)}
                        </Select>
                        {errors.form_ways && <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>{errors.form_ways}</CoreModules.FormLabel>}

                    </CoreModules.FormControl>

                    {values.form_ways === 'Upload a Custom Form' ? <>
                        <a download>Download Form Template <CoreModules.IconButton style={{ borderRadius: 0 }} color="primary" component="label">
                            <AssetModules.FileDownloadIcon style={{ color: '#2DCB70' }} />
                        </CoreModules.IconButton></a>
                        <CoreModules.FormLabel>Upload XLS Form</CoreModules.FormLabel>
                        <CoreModules.Button
                            variant="contained"
                            component="label"
                        >
                            <CoreModules.Input
                                type="file"
                                onChange={(e) => {
                                    handleCustomChange('uploaded_form', e.target.files)
                                    // setFormFileUpload(e.target.files)
                                }}
                            />
                        </CoreModules.Button>
                        {!values.uploaded_form && <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>Form File is required.</CoreModules.FormLabel>}
                    </> : null}

                    <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', width: '100%', justifyContent: 'space-between' }}>
                        {/* Previous Button  */}
                        <Link to="/create-project">
                            <CoreModules.Button
                                sx={{ width: '150px' }}
                                variant="outlined"
                                color="error"
                            >
                                Previous
                            </CoreModules.Button>
                        </Link>
                        {/* END */}

                        {/* Submit Button For Create Project on Area Upload */}
                        <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <CoreModules.Button
                                sx={{ width: '150px' }}
                                variant="contained"
                                color="error"
                                type="submit"
                            // disabled={!fileUpload ? true : false}

                            >
                                Next
                            </CoreModules.Button>
                        </CoreModules.Stack>
                        {/* END */}
                    </CoreModules.Stack>
                </FormGroup>
            </form>
        </CoreModules.Stack >
    )
};
export default FormSelection;
