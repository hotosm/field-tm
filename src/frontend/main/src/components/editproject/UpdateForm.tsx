import React, { useEffect, useState } from 'react';
import CoreModules from '../../shared/CoreModules';
import environment from '../../environment';
import { FormCategoryService, PostFormUpdate } from '../../api/CreateProjectService';
import { MenuItem } from '@mui/material';
import { diffObject } from '../../utilfunctions/compareUtils.js';

const UpdateForm = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();
  const editProjectDetails: any = CoreModules.useAppSelector((state) => state.createproject.editProjectDetails);
  const [uploadForm, setUploadForm] = useState(null);
  const [selectedFormCategory, setSelectedFormCategory] = useState(null);
  const formUpdateLoading: any = CoreModules.useAppSelector((state) => state.createproject.formUpdateLoading);

  const formCategoryList = CoreModules.useAppSelector((state) => state.createproject.formCategoryList);
  const previousXform_title = CoreModules.useAppSelector((state) => state.project.projectInfo.xform_title);
  const formCategoryData = formCategoryList.map((item) => ({ label: item.title, value: item.title }));

  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  //we use use selector from redux to get all state of defaultTheme from theme slice

  // Fetching form category list
  useEffect(() => {
    dispatch(FormCategoryService(`${environment.baseApiUrl}/central/list-forms`));
  }, []);

  const onSubmit = () => {
    const diffPayload = diffObject({ category: previousXform_title }, { category: selectedFormCategory });
    console.log(diffPayload, 'diffPayload');

    dispatch(
      PostFormUpdate(`${environment.baseApiUrl}/projects/update_category`, {
        ...(Object.keys(diffPayload).length > 0 ? diffPayload : { category: selectedFormCategory }),
        project_id: projectId,
        upload: uploadForm,
      }),
    );
  };
  useEffect(() => {
    setSelectedFormCategory(previousXform_title);
  }, [previousXform_title]);

  return (
    <CoreModules.Stack sx={{ width: '20%' }}>
      <CoreModules.FormControl sx={{ mb: 3 }}>
        <CoreModules.FormLabel>Form Category</CoreModules.FormLabel>

        <CoreModules.Select
          labelId="form_category-label"
          id="form_category"
          value={selectedFormCategory}
          label="Form Category"
          // sx={{
          //   '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          //     border: '2px solid black',
          //   },
          // }}
          onChange={(e) => {
            setSelectedFormCategory(e.target.value);
            // handleCustomChange('xform_title', e.target.value);
            // dispatch(
            //   CreateProjectActions.SetIndividualProjectDetailsData({
            //     ...projectDetails,
            //     xform_title: e.target.value,
            //   }),
            // );
          }}
          inputProps={{ shrink: selectedFormCategory ? true : false }}
        >
          {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
          {formCategoryData?.map((form) => (
            <MenuItem key={form.value} value={form.value}>
              {form.label}
            </MenuItem>
          ))}
        </CoreModules.Select>
        {/* {errors.xform_title && (
          <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
            {errors.xform_title}
          </CoreModules.FormLabel>
        )} */}
      </CoreModules.FormControl>
      <CoreModules.FormLabel>Upload .xls/.xlsx/.xml Form</CoreModules.FormLabel>
      <CoreModules.Button variant="contained" component="label">
        <CoreModules.Input
          type="file"
          onChange={(e) => {
            setUploadForm(e.target.files[0]);
          }}
          inputProps={{ accept: '.xml, .xls, .xlsx' }}
        />
        {/* <CoreModules.Typography component="h4">{customFormFile?.name}</CoreModules.Typography> */}
      </CoreModules.Button>
      {/* {!values.uploaded_form && (
          <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
            Form File is required.
          </CoreModules.FormLabel>
        )} */}
      <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
        <CoreModules.LoadingButton
          disabled={formUpdateLoading}
          type="button"
          loading={formUpdateLoading}
          loadingPosition="end"
          // endIcon={<AssetModules.SettingsSuggestIcon />}
          variant="contained"
          color="error"
          onClick={onSubmit}
        >
          Submit
        </CoreModules.LoadingButton>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default UpdateForm;
