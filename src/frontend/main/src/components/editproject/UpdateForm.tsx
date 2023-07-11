import React, { useState } from 'react'
import CoreModules from '../../shared/CoreModules';
import environment from '../../environment';
import { PostFormUpdate } from '../../api/CreateProjectService';

const UpdateForm = ({projectId}) => {
  const dispatch = CoreModules.useDispatch();
  const [uploadForm, setUploadForm] = useState(null);
  const formUpdateLoading: any = CoreModules.useSelector<any>((state) => state.createproject.formUpdateLoading);
  // //we use use selector from redux to get all state of defaultTheme from theme slice
  const onSubmit=()=>{
    dispatch(PostFormUpdate(`${environment.baseApiUrl}/projects/update-form/${projectId}`,uploadForm));
  }
  return (
    <CoreModules.Stack sx={{width:'30%'}}>
        <CoreModules.FormLabel>Upload .xls/.xlsx/.xml Form</CoreModules.FormLabel>
        <CoreModules.Button variant="contained" component="label">
          <CoreModules.Input
            type="file"
            onChange={(e) => {
              setUploadForm(e.target.files[0]);
            }}
            inputProps={{ "accept":".xml, .xls, .xlsx" }}

          />
          {/* <CoreModules.Typography component="h4">{customFormFile?.name}</CoreModules.Typography> */}
        </CoreModules.Button>
        {/* {!values.uploaded_form && (
          <CoreModules.FormLabel component="h3" sx={{ mt: 2, color: defaultTheme.palette.error.main }}>
            Form File is required.
          </CoreModules.FormLabel>
        )} */}
        <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end', mt:4 }}> 
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