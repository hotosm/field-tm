import React, { useEffect } from 'react';
import AssetModules from '@/shared/AssetModules';
import ProjectInfo from '@/components/ProjectSubmissions/ProjectInfo.js';
import SubmissionsInfographics from '@/components/ProjectSubmissions/SubmissionsInfographics.js';
import SubmissionsTable from '@/components/ProjectSubmissions/SubmissionsTable.js';
import CoreModules from '@/shared/CoreModules';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { ProjectById, GetEntityInfo } from '@/api/Project';
import { useSearchParams } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import { ProjectContributorsService, MappedVsValidatedTaskService } from '@/api/SubmissionService';

const ProjectSubmissions = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const projectId = params.projectId;

  const state = useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const entityList = useAppSelector((state) => state.project.entityOsmMap);
  const updatedEntities = entityList?.filter((entity) => entity?.status > 1);

  //Fetch project for the first time
  useEffect(() => {
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == projectId) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != projectId) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);

  // for hot fix to display task-list and show option of task-list for submission table filter
  // better solution needs to be researched
  useEffect(() => {
    dispatch(GetEntityInfo(`${import.meta.env.VITE_API_URL}/projects/${projectId}/entities/statuses`));
  }, []);

  useEffect(() => {
    dispatch(ProjectContributorsService(`${import.meta.env.VITE_API_URL}/projects/contributors/${projectId}`));
  }, []);

  useEffect(() => {
    dispatch(
      MappedVsValidatedTaskService(`${import.meta.env.VITE_API_URL}/tasks/activity/?project_id=${projectId}&days=30`),
    );
  }, []);

  useEffect(() => {
    if (!searchParams.get('tab')) {
      setSearchParams({ tab: 'infographics' });
    }
  }, []);

  const ToggleView = () => (
    <div className="fmtm-flex fmtm-justify-end fmtm-gap-3">
      <div title="Infographics View">
        <AssetModules.GridViewIcon
          style={{ fontSize: '30px' }}
          className={`${
            searchParams.get('tab') === 'infographics' ? 'fmtm-text-primaryRed' : 'fmtm-text-[#545454]'
          } hover:fmtm-text-primaryRed fmtm-cursor-pointer`}
          onClick={() => {
            setSearchParams({ tab: 'infographics' });
          }}
        />
      </div>
      <div title="Table View">
        <AssetModules.ListAltIcon
          style={{ fontSize: '30px' }}
          className={`${
            searchParams.get('tab') === 'table' ? 'fmtm-text-primaryRed' : 'fmtm-text-[#545454]'
          } hover:fmtm-text-primaryRed fmtm-cursor-pointer`}
          onClick={() => {
            setSearchParams({ tab: 'table' });
          }}
        />
      </div>
    </div>
  );

  return (
    <div className="fmtm-bg-[#F5F5F5]">
      <div className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row fmtm-mb-4 fmtm-w-full">
        <ProjectInfo entities={updatedEntities} />
      </div>
      <div className="fmtm-w-full">
        {searchParams.get('tab') === 'infographics' ? (
          <SubmissionsInfographics toggleView={<ToggleView />} entities={updatedEntities} />
        ) : (
          <SubmissionsTable toggleView={<ToggleView />} />
        )}
      </div>
    </div>
  );
};

export default ProjectSubmissions;
