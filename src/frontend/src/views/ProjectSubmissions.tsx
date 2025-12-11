import React, { useEffect } from 'react';
import ProjectInfo from '@/components/ProjectSubmissions/ProjectInfo.js';
import SubmissionsInfographics from '@/components/ProjectSubmissions/Infographics';
import SubmissionsTable from '@/components/ProjectSubmissions/Table';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { ProjectById, GetEntityStatusList } from '@/api/Project';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { ProjectContributorsService, MappedVsValidatedTaskService } from '@/api/SubmissionService';
import TableChartViewIcon from '@/components/Icons/TableChartViewIcon';
import TableIcon from '@/components/Icons/TableIcon';
import { Tooltip } from '@mui/material';
import { field_mapping_app } from '@/types/enums';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ProjectSubmissions = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const projectId = params.projectId;
  const tab = searchParams.get('tab');

  const state = useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const projectDetailsLoading = useAppSelector((state) => state.project.projectDetailsLoading);
  const entityList = useAppSelector((state) => state.project.entityOsmMap);
  const updatedEntities = entityList?.filter((entity) => entity?.status > 1);

  useEffect(() => {
    if (projectInfo.field_mapping_app === field_mapping_app.QField && !projectDetailsLoading) {
      navigate(`/project/${projectId}`);
    }
  }, [projectInfo, projectDetailsLoading]);

  //Fetch project for the first time
  useEffect(() => {
    if (!projectId) return;
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == +projectId) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != +projectId) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);

  // for hot fix to display task-list and show option of task-list for submission table filter
  // better solution needs to be researched
  useEffect(() => {
    dispatch(GetEntityStatusList(`${VITE_API_URL}/projects/${projectId}/entities/statuses`));
  }, []);

  useEffect(() => {
    dispatch(ProjectContributorsService(`${VITE_API_URL}/projects/contributors/${projectId}`));
  }, []);

  useEffect(() => {
    dispatch(MappedVsValidatedTaskService(`${VITE_API_URL}/tasks/activity?project_id=${projectId}&days=30`));
  }, []);

  useEffect(() => {
    if (!searchParams.get('tab')) {
      setSearchParams({ tab: 'table' });
    }
  }, []);

  const ToggleView = () => (
    <div className="fmtm-flex fmtm-border fmtm-border-grey-200 fmtm-rounded-lg fmtm-w-fit fmtm-ml-auto fmtm-overflow-hidden">
      <Tooltip title="Infographics View" placement="bottom" arrow>
        <div
          className={`fmtm-p-2 fmtm-cursor-pointer hover:fmtm-bg-red-light ${tab === 'infographics' ? 'fmtm-bg-red-light fmtm-text-red-medium' : 'fmtm-text-grey-800'}`}
          onClick={() => {
            setSearchParams({ tab: 'infographics' });
          }}
        >
          <TableChartViewIcon fillColor={`${tab === 'infographics' ? '#D73F37' : '#484848'}`} size={20} />
        </div>
      </Tooltip>
      <Tooltip title="Table View" placement="bottom" arrow>
        <div
          className={`fmtm-p-2 fmtm-border-l fmtm-border-grey-200 fmtm-cursor-pointer hover:fmtm-bg-red-light ${tab === 'table' ? 'fmtm-bg-red-light fmtm-text-red-medium' : 'fmtm-text-grey-800'}`}
          onClick={() => {
            setSearchParams({ tab: 'table' });
          }}
        >
          <TableIcon fillColor={`${tab === 'table' ? '#D73F37' : '#484848'}`} size={20} />
        </div>
      </Tooltip>
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
