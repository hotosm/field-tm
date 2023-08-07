import React from 'react'
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules';
import useForm from '../../hooks/useForm';
import EditProjectValidation from './validation/EditProjectDetailsValidation';
import { diffObject } from '../../utilfunctions/compareUtils'
import environment from '../../environment';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { PatchProjectDetails } from '../../api/CreateProjectService';
const EditProjectDetails = ({projectId}) => {
  const editProjectDetails: any = CoreModules.useSelector<any>((state) => state.createproject.editProjectDetails);
  // //we use use selector from redux to get all state of projectDetails from createProject slice

  const organizationListData: any = CoreModules.useSelector<any>((state) => state.createproject.organizationList);
  // //we use use selector from redux to get all state of projectDetails from createProject slice
  
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  // //we use use selector from redux to get all state of defaultTheme from theme slice

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  const submission = () => {
    // eslint-disable-next-line no-use-before-define
    // submitForm();
    const changedValues = diffObject(editProjectDetails,values);
    dispatch(CreateProjectActions.SetIndividualProjectDetails(values));
    if(Object.keys(changedValues).length>0){
      dispatch(PatchProjectDetails(`${environment.baseApiUrl}/projects/${projectId}`,changedValues));
    }
  };

  const { handleSubmit,handleChange, handleCustomChange, values, errors }: any = useForm(
    editProjectDetails,
    submission,
    EditProjectValidation,
  );
  const organizationList = organizationListData.map((item) => ({ label: item.name, value: item.id }));
  const inputFormStyles = () => {
    return {
      style: {
        color: defaultTheme.palette.error.main,
        fontFamily: defaultTheme.typography.fontFamily,
        fontSize: defaultTheme.typography.fontSize,
      }, // or className: 'your-class'
    };
  };
  return (
    <CoreModules.Stack>
       <form onSubmit={handleSubmit} style={{ paddingBottom: '4rem' }}>
        <CoreModules.FormGroup>
          {/* Organization Dropdown For Edit Project */}
          {/* <CoreModules.FormControl sx={{ mb: 0, width: { md: '50%', lg: '30%' } }} variant="outlined">
            <CoreModules.Box
              sx={{
                display: 'flex',
                flexDirection: 'row',
                pt: 0,
              }}
            >
              <CoreModules.FormLabel
                component="h3"
                sx={{
                  '&.Mui-focused': {
                    color: 'black',
                  },
                }}
              >
                Organization
              </CoreModules.FormLabel>
              <CoreModules.FormLabel
                component="h3"
                sx={{
                  color: 'red',
                  '&.Mui-focused': {
                    color: 'red',
                  },
                }}
              >
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.Stack
              sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center' }}
            >
              <CoreModules.Select
                inputProps={{ sx: { padding: '8.5px 14px' } }}
                sx={{
                  width: '100%',
                  '&.Mui-focused': {
                    border: '2px solid black',
                  },
                }}
                labelId="demo-simple-select-label"
                id="demo-simple-select"
                value={values.organization || ''}
                onChange={(e) => {
                  handleCustomChange('organization', e.target.value);                }}
              >
                {organizationList?.map((org) => (
                  <MenuItem value={org.value}>{org.label}</MenuItem>
                ))}
              </CoreModules.Select>
            </CoreModules.Stack>
            {errors.organization && (
              <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                {errors.organization}
              </CoreModules.FormLabel>
            )}
          </CoreModules.FormControl> */}

          {/* END */}

         
          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 0, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
              <CoreModules.FormLabel component="h3">Project Name</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="name"
              name="name"
              type="name"
              autoComplete="on"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.name}
              onChange={(e) => {
                handleChange(e);
              }}
              helperText={errors.name}
              FormHelperTextProps={inputFormStyles()}
            />
          </CoreModules.FormControl>

          {/* Short Description Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 3, width: { md: '50%', lg: '50%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Short Description</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="short_description"
              name="short_description"
              label=""
              variant="outlined"
              value={values.short_description}
              onChange={(e) => {
                handleChange(e);
              }}
              multiline
              rows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              helperText={errors.short_description}
              FormHelperTextProps={inputFormStyles()}
            />
          </CoreModules.FormControl>
          {/* END */}

          {/* Description Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 3, width: { md: '50%', lg: '50%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Description</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="description"
              label=""
              name="description"
              variant="outlined"
              value={values.description}
              onChange={(e) => {
                handleChange(e);
              }}
              multiline
              rows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              helperText={errors.description}
              FormHelperTextProps={inputFormStyles()}
            />
          </CoreModules.FormControl>
          {/* END */}

          <CoreModules.Box
            sx={{
              display: 'flex',
              width: { xs: 'full', md: '50%' },
              justifyContent: 'center',
            }}
          >
            {/* Form Submission Button For Create Project */}
            <CoreModules.Button variant="contained" color="error" sx={{ width: '10%' }} type="submit">
              Save
            </CoreModules.Button>
            {/* END */}
          </CoreModules.Box>
        </CoreModules.FormGroup>
      </form>
    </CoreModules.Stack>
  )
}


export default EditProjectDetails