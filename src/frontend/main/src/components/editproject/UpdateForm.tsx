import React, { useEffect, useState } from 'react'
import CoreModules from '../../shared/CoreModules';
import environment from '../../environment';
import { PostFormUpdate } from '../../api/CreateProjectService';

const UpdateForm = ({ projectId }) => {
  const dispatch = CoreModules.useDispatch();
  const editProjectDetails: any = CoreModules.useSelector<any>((state) => state.createproject.editProjectDetails);
  const [uploadForm, setUploadForm] = useState(null);
  const [formUpdateOption, setFormUpdateOption] = useState<any>(null);
  const formUpdateLoading: any = CoreModules.useSelector<any>((state) => state.createproject.formUpdateLoading);
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  // //we use use selector from redux to get all state of defaultTheme from theme slice
  const selectFormWaysList = ['Use Existing Form', 'Upload a Custom Form'];
  const selectFormWays = selectFormWaysList.map((item) => ({ label: item, value: item }));
  const formCategoryList = CoreModules.useSelector((state: any) => state.createproject.formCategoryList);
  // //we use use-selector from redux to get all state of formCategory from createProject slice
  const formCategoryData = formCategoryList.map((item) => ({ label: item.title, value: item.title }));

  useEffect(() => {
    setFormUpdateOption({ ...formUpdateOption, formCategory: editProjectDetails?.xform_title });
  }, [editProjectDetails])


  const onSubmit = () => {
    dispatch(PostFormUpdate(`${environment.baseApiUrl}/projects/update_category?project_id=${projectId}&category=${formUpdateOption?.formCategory}`, uploadForm));
  }
  return (
    <CoreModules.Stack sx={{ width: '50%' }}>

      {/* {!values.uploaded_form && (
          <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
            Form File is required.
          </CoreModules.FormLabel>
        )} */}

      <CoreModules.FormControl sx={{ mb: 3 }}>
        <CoreModules.InputLabel
          id="form-category"
          sx={{
            '&.Mui-focused': {
              color: defaultTheme.palette.black,
            },
          }}
        >
          Form Selection
        </CoreModules.InputLabel>
        <CoreModules.Select
          labelId="form_ways-label"
          id="form_ways"
          // value={values.form_ways}
          label="Form Selection"
          sx={{
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              border: '2px solid black',
            },
          }}
          onChange={(e) => {
            setFormUpdateOption({ ...formUpdateOption, formWays: e.target.value });
            // handleCustomChange('form_ways', e.target.value);
            // dispatch(
            //   CreateProjectActions.SetIndividualProjectDetailsData({
            //     ...projectDetails,
            //     form_ways: e.target.value,
            //   }),
            // );
          }}
        // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'form_ways', value: e.target.value }))}
        >
          {selectFormWays?.map((form) => (
            <CoreModules.MenuItem value={form.value}>{form.label}</CoreModules.MenuItem>
          ))}
        </CoreModules.Select>
        {/* {errors.form_ways && (
          <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
            {errors.form_ways}
          </CoreModules.FormLabel>
        )} */}

        <CoreModules.FormControl sx={{ my: 3 }}>
          <CoreModules.InputLabel
            id="form-category"
            sx={{
              '&.Mui-focused': {
                color: defaultTheme.palette.black,
              },
            }}
          >
            Form Category
          </CoreModules.InputLabel>
          <CoreModules.Select
            labelId="form_category-label"
            id="form_category"
            value={editProjectDetails?.xform_title}
            label="Form Category"
            sx={{
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                border: '2px solid black',
              },
            }}
            onChange={(e) => {
              setFormUpdateOption({ ...formUpdateOption, formCategory: e.target.value });
            }}
          >
            {/* onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value: e.target.value }))} > */}
            {formCategoryData?.map((form) => (
              <CoreModules.MenuItem PaperProps={{
                style: {
                  marginTop: "40px"
                }
              }} sx={{
                height: '40px',
                maxHeight: "calc(100% - 633px)"
              }} value={form.value}>{form.label}</CoreModules.MenuItem>
            ))}
          </CoreModules.Select>
          {/* {errors.xform_title && (
            <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
              {errors.xform_title}
            </CoreModules.FormLabel>
          )} */}
        </CoreModules.FormControl>

        {formUpdateOption?.formWays === 'Upload a Custom Form' ? <CoreModules.FormControl sx={{ mt: 5 }}>
          <CoreModules.FormLabel>Upload .xls/.xlsx/.xml Form</CoreModules.FormLabel>
          <CoreModules.Button variant="contained" component="label">
            <CoreModules.Input
              type="file"
              onChange={(e) => {
                setUploadForm(e.target.files[0]);
              }}
              inputProps={{ "accept": ".xml, .xls, .xlsx" }}

            />
            {/* <CoreModules.Typography component="h4">{customFormFile?.name}</CoreModules.Typography> */}
          </CoreModules.Button>
        </CoreModules.FormControl> : null}

      </CoreModules.FormControl>
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
  )
}

export default UpdateForm