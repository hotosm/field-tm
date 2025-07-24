import React, { useEffect } from 'react';
import AssetModules from '@/shared/AssetModules';
import ProjectInfo from '@/components/ProjectSubmissions/ProjectInfo.js';
import SubmissionsInfographics from '@/components/ProjectSubmissions/SubmissionsInfographics.js';
import SubmissionsTable from '@/components/ProjectSubmissions/SubmissionsTable.js';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { ProjectById, GetEntityStatusList } from '@/api/Project';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import {
  ProjectContributorsService,
  MappedVsValidatedTaskService,
  SubmissionFormFieldsService,
} from '@/api/SubmissionService';
import TableChartViewIcon from '@/components/Icons/TableChartViewIcon';
import TableIcon from '@/components/Icons/TableIcon';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ProjectSubmissions = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const projectId = params.projectId;
  const tab = searchParams.get('tab');

  const state = useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const entityList = useAppSelector((state) => state.project.entityOsmMap);
  const updatedEntities = entityList?.filter((entity) => entity?.status > 1);

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
    dispatch(SubmissionFormFieldsService(`${VITE_API_URL}/submission/submission-form-fields?project_id=${projectId}`));
  }, []);

  useEffect(() => {
    if (!searchParams.get('tab')) {
      setSearchParams({ tab: 'table' });
    }
  }, []);

  const ToggleView = () => (
    <div className="fmtm-flex fmtm-border fmtm-border-grey-200 fmtm-rounded-lg fmtm-w-fit fmtm-ml-auto">
      <div
        className={`fmtm-p-2 fmtm-cursor-pointer hover:fmtm-bg-red-light ${tab === 'infographics' ? 'fmtm-bg-red-light fmtm-text-red-medium' : 'fmtm-text-grey-800'}`}
        onClick={() => {
          setSearchParams({ tab: 'infographics' });
        }}
      >
        <TableChartViewIcon fillColor={`${tab === 'infographics' ? '#D73F37' : '#484848'}`} size={20} />
      </div>
      <div
        className={`fmtm-p-2 fmtm-border-l fmtm-border-grey-200 fmtm-cursor-pointer hover:fmtm-bg-red-light ${tab === 'table' ? 'fmtm-bg-red-light fmtm-text-red-medium' : 'fmtm-text-grey-800'}`}
        onClick={() => {
          setSearchParams({ tab: 'table' });
        }}
      >
        <TableIcon fillColor={`${tab === 'table' ? '#D73F37' : '#484848'}`} size={20} />
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
