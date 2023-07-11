import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import CoreModules from '../shared/CoreModules';
import { useDispatch } from 'react-redux';
import environment from '../environment';
import { GetIndividualProjectDetails, OrganisationService } from '../api/CreateProjectService';
import EditProjectDetails from '../components/editproject/EditProjectDetails';
import SidebarContent from '../constants/EditProjectSidebarContent';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import UpdateForm from '../components/editproject/UpdateForm';

const EditProject: React.FC = () => {
  const dispatch = useDispatch(); 
  const [selectedTab, setSelectedTab]= useState('project-description');
  const params = CoreModules.useParams();
  const encodedProjectId = params.projectId;
  const decodedProjectId = environment.decode(encodedProjectId);
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  const tabHover = {
    '&:hover': {
      background: defaultTheme.palette.grey.light,
      cursor:'pointer'
    },
  };
  useEffect(() => {
    dispatch(OrganisationService(`${environment.baseApiUrl}/organization/`));

    if(decodedProjectId){
      dispatch(GetIndividualProjectDetails(`${environment.baseApiUrl}/projects/${decodedProjectId}`));
    }
  }, [decodedProjectId])

// useEffect(() => {
//   if(!editProjectResponse)return;
//   const encodedProjectId= environment.encode(editProjectResponse.id);
//   navigate(`/project_details/${encodedProjectId}`);
//   dispatch(CreateProjectActions.SetPatchProjectDetails(null));
// }, [editProjectResponse])

  return (
    <div>
      <CoreModules.Stack>
        <CoreModules.Typography variant="subtitle2" color={'info'} noWrap sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          position: 'sticky',
          top: 0,
          background: 'white',
          zIndex: 1,
          paddingBottom: '1.5rem',
        }} ml={'3%'}>
          Edit Project
        </CoreModules.Typography>
        <CoreModules.Stack flexDirection="row">
          <CoreModules.Stack sx={{m:4, display:'flex', flex: '30%',gap:1}}>
            {SidebarContent.map((content)=>
              <CoreModules.Typography onClick={()=>setSelectedTab(content.slug)} sx={{p:1, ...tabHover, backgroundColor:selectedTab === content.slug ? defaultTheme.palette.grey.light : 'white'}}    variant="subtitle2">
                {content.name}
              </CoreModules.Typography>
            )}
          </CoreModules.Stack>
          <CoreModules.Stack sx={{display:'flex', flex: '70%',p:3}}>
            {selectedTab === 'project-description' ?<EditProjectDetails projectId={decodedProjectId} />:null}
            {selectedTab === 'form-update' ?<UpdateForm projectId={decodedProjectId}/>:null}
          </CoreModules.Stack>
        </CoreModules.Stack>
      </CoreModules.Stack>
    </div>
  );
};

export default EditProject;
