import React,{ useEffect } from "react";
import '../styles/home.css'
import CoreModules from "../shared/CoreModules";
import UploadArea from "../components/createproject/UploadArea";
import { useLocation, useNavigate } from 'react-router-dom';
import ProjectDetailsForm from "../components/createproject/ProjectDetailsForm";

const CreateProject = () => {
  const location= useLocation();

  // history.push(path);
    // const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension


    // const theme = CoreModules.useSelector(state => state.theme.hotTheme)
    // useEffect(() => {
    //     dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
    //     //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    // }, [])
  
   
    return (
        <div style={{ padding: 7 }}>
            <CoreModules.Stack sx={{display:'flex',justifyContent:'center',alignItems:'center',flexDirection:'row',}}>
              <CoreModules.Typography
                variant="subtitle2"
                color={'info'}
                noWrap
                sx={{ display: { xs: 'none', sm: 'block', } }}
                ml={'3%'}
              >
                Create New Project
              </CoreModules.Typography>
            </CoreModules.Stack>
            <CoreModules.Stack sx={{paddingLeft:'13rem',paddingTop:'6rem'}} direction="row" spacing={13}>
              
              <CoreModules.Stack spacing={2}>
              {/* Project Details SideBar Button for Creating Project */}
                <CoreModules.Button 
                  variant="contained"
                  color="error"
                  disabled={location.pathname !== '/create-project'}
                  >
                    Project Details
                </CoreModules.Button>

                {/* END */}

                {/* Upload Area SideBar Button for uploading Area page  */}
                <CoreModules.Button 
                  variant="contained"
                  color="error"
                  disabled={location.pathname !== '/upload-area'}
                  >
                    Upload Area
                </CoreModules.Button>
                {/* END */}

              </CoreModules.Stack>
              {/* Showing Different Create Project Component When the url pathname changes */}

                {location.pathname === "/create-project" ? <ProjectDetailsForm />:null}
                {location.pathname === "/upload-area" ? <UploadArea />:null}
              {/* END */}
            
            </CoreModules.Stack>
           
        </div>
    )

}

export default CreateProject;
