import React,{ useEffect } from "react";
import windowDimention from "../../hooks/WindowDimension";
import enviroment from "../../environment";
import CoreModules from "../../shared/CoreModules";
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { CreateProjectService } from "../../api/CreateProjectService";
import { useNavigate } from 'react-router-dom';

const ProjectDetailsForm = () => {
    // const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
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
    const onCreateProjectSubmission =()=>{
        dispatch(CreateProjectService(`${enviroment.baseApiUrl}/projects/create_project`,
            {"project_info": {...projectDetails},
                "author": {
                    "username": projectDetails.username,
                    "id": projectDetails.id
                },
            }
        ));
    }
    // Might Need To Fix little after all backend PR merges  // 
      
    useEffect(() => {
        if(projectDetailsResponse !== null){
            navigate('/upload-area');
        }

    }, [projectDetailsResponse])
    return (
        <CoreModules.Stack sx={{width:'50%'}}>
        <CoreModules.FormGroup>
            {/* User Id Form Input For Create Project  as Oauth is Not Working   "FIX ME" */}
            <CoreModules.FormControl sx={{mb:3}}>
                <CoreModules.FormLabel component="h3">User Id *</CoreModules.FormLabel>
                <CoreModules.TextField
                    id="id"
                    label=""
                    variant="filled"
                    inputProps={{sx:{padding:'8.5px 14px'}}}
                    value={projectDetails.id}
                        onChange={(e)=>{
                        dispatch(CreateProjectActions.SetProjectDetails({key:'id',value:e.target.value}));
                    }}
                />
            </CoreModules.FormControl>
            {/* END */}

            {/* User Name Form Input For Create Project  as Oauth is Not Working   "FIX ME" */}
            <CoreModules.FormControl sx={{mb:3}}>
                <CoreModules.FormLabel component="h3">Username *</CoreModules.FormLabel>
                <CoreModules.TextField
                    id="username"
                    label=""
                    variant="filled"
                    inputProps={{sx:{padding:'8.5px 14px'}}}
                    value={projectDetails.username}
                    onChange={(e)=>{
                        dispatch(CreateProjectActions.SetProjectDetails({key:'username',value:e.target.value}));
                    }}
                />
            </CoreModules.FormControl>
            {/* END */}

            {/* Project Name Form Input For Create Project */}
            <CoreModules.FormControl sx={{mb:3}}>
                <CoreModules.FormLabel component="h3">Project Name *</CoreModules.FormLabel>
                <CoreModules.TextField
                    id="project_name"
                    label=""
                    variant="filled"
                    inputProps={{sx:{padding:'8.5px 14px'}}}
                    value={projectDetails.name}
                        onChange={(e)=>{
                        dispatch(CreateProjectActions.SetProjectDetails({key:'name',value:e.target.value}));
                    }}
                />
            </CoreModules.FormControl>
            {/* END */}

            {/* Short Description Form Input For Create Project */}
            <CoreModules.FormControl sx={{mb:3}}>
                <CoreModules.FormLabel component="h3">Short Description</CoreModules.FormLabel>
                <CoreModules.TextField
                    id="short_description"
                    label=""
                    variant="filled"
                    value={projectDetails.short_description}
                    onChange={(e)=>{
                        dispatch(CreateProjectActions.SetProjectDetails({key:'short_description',value:e.target.value}));
                    }}
                    multiline
                    rows={4}
                />
            </CoreModules.FormControl>
            {/* END */}

            {/* Description Form Input For Create Project */}
            <CoreModules.FormControl sx={{mb:3}}>
                <CoreModules.FormLabel component="h3">Description</CoreModules.FormLabel>
                <CoreModules.TextField
                    id="description"
                    label=""
                    variant="filled"
                    value={projectDetails.description}
                    onChange={(e)=>{
                        dispatch(CreateProjectActions.SetProjectDetails({key:'description',value:e.target.value}));
                    }}
                    multiline
                    rows={4} 
                    //  onChange={}
                />
            </CoreModules.FormControl>
            {/* END */}

            <CoreModules.Box sx={{display:'flex',justifyContent:'flex-end',alignItems:'flex-end'}}>
                {/* Form Submission Button For Create Project */}
                <CoreModules.Button 
                    variant="contained"
                    color="error"
                    sx={{width:'20%'}}
                    onClick={onCreateProjectSubmission}
                    >
                    Next
                </CoreModules.Button>
                {/* END */}
            </CoreModules.Box>
        </CoreModules.FormGroup>
        </CoreModules.Stack>
    )
};
export default ProjectDetailsForm;
