import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import environment from '../environment';
import { FormCategoryService, GetIndividualProjectDetails, OrganisationService } from '../api/CreateProjectService';
import EditProjectDetails from '../components/editproject/EditProjectDetails';
import SidebarContent from '../constants/EditProjectSidebarContent';
import { useNavigate } from 'react-router-dom';
import UpdateForm from '../components/editproject/UpdateForm';
import UpdateProjectArea from '../components/editproject/UpdateProjectArea';

const EditProject: React.FC = () => {
  const dispatch = CoreModules.useDispatch();
  const [selectedTab, setSelectedTab] = useState('project-description');
  const params = CoreModules.useParams();
  const navigate = useNavigate();
  const encodedProjectId = params.projectId;
  const decodedProjectId = environment.decode(encodedProjectId);
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  const tabHover = {
    '&:hover': {
      background: defaultTheme.palette.grey.light,
      cursor: 'pointer',
    },
  };
  useEffect(() => {
    dispatch(OrganisationService(`${environment.baseApiUrl}/organization/`));

    if (decodedProjectId) {
      dispatch(GetIndividualProjectDetails(`${environment.baseApiUrl}/projects/${decodedProjectId}`));
    }
  }, [decodedProjectId]);

  return (
    <div>
      <CoreModules.Stack>
        <CoreModules.Stack flexDirection="row">
          <CoreModules.IconButton
            sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '80px', ml: 3 }}
            onClick={() => {
              navigate(-1);
              // setOpen(true);
            }}
            color="info"
          >
            <AssetModules.ArrowBackIcon color="info" sx={{ fontSize: '30px' }} />
            <CoreModules.Typography ml={2} variant="h1">
              Back
            </CoreModules.Typography>
          </CoreModules.IconButton>
          <CoreModules.Typography
            variant="subtitle2"
            color={'info'}
            sx={{
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
            }}
            ml={'3%'}
            mt={3}
          >
            Edit Project
          </CoreModules.Typography>
        </CoreModules.Stack>
        <CoreModules.Stack flexDirection="row">
          <CoreModules.Stack sx={{ m: 4, display: 'flex', flex: '20%', gap: 1 }}>
            {SidebarContent.map((content) => (
              <CoreModules.Typography
                key={content.slug}
                onClick={() => setSelectedTab(content.slug)}
                sx={{
                  p: 1,
                  ...tabHover,
                  backgroundColor: selectedTab === content.slug ? defaultTheme.palette.grey.light : 'white',
                }}
                variant="subtitle2"
              >
                {content.name}
              </CoreModules.Typography>
            ))}
          </CoreModules.Stack>
          <CoreModules.Stack sx={{ display: 'flex', flex: '80%', p: 3 }}>
            {selectedTab === 'project-description' ? <EditProjectDetails projectId={decodedProjectId} /> : null}
            {selectedTab === 'form-update' ? <UpdateForm projectId={decodedProjectId} /> : null}
            {selectedTab === 'update-project-boundary' ? <UpdateProjectArea projectId={decodedProjectId} /> : null}
          </CoreModules.Stack>
        </CoreModules.Stack>
      </CoreModules.Stack>
    </div>
  );
};

export default EditProject;
