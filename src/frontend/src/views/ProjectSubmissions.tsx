import React, { useEffect, useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import ProjectInfo from '@/components/ProjectSubmissions/ProjectInfo.js';
import SubmissionsInfographics from '@/components/ProjectSubmissions/SubmissionsInfographics.js';
import SubmissionsTable from '@/components/ProjectSubmissions/SubmissionsTable.js';
import CoreModules from '@/shared/CoreModules';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { ProjectById } from '@/api/Project';
import environment from '@/environment';
import { fetchInfoTask } from '@/api/task';
import { GetProjectDashboard } from '@/api/Project';
import { useSearchParams } from 'react-router-dom';

const ProjectSubmissions = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const encodedId = params.projectId;
  const decodedId = environment.decode(encodedId);

  const state = CoreModules.useAppSelector((state) => state.project);
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);

  //Fetch project for the first time
  useEffect(() => {
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(encodedId)) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);

  useEffect(() => {
    const fetchData = () => {
      dispatch(fetchInfoTask(`${import.meta.env.VITE_API_URL}/tasks/tasks-features/?project_id=${decodedId}`));
    };
    fetchData();
  }, []);

  useEffect(() => {
    dispatch(GetProjectDashboard(`${import.meta.env.VITE_API_URL}/projects/project_dashboard/${decodedId}`));
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
    <div className="fmtm-bg-[#F5F5F5] fmtm-px-5 sm:fmtm-px-5 lg:fmtm-px-8 xl:fmtm-px-16 fmtm-pb-5">
      <div className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row fmtm-my-4 fmtm-w-full">
        <ProjectInfo />
      </div>
      <div className="fmtm-w-full">
        {searchParams.get('tab') === 'infographics' ? (
          <SubmissionsInfographics toggleView={<ToggleView />} />
        ) : (
          <SubmissionsTable toggleView={<ToggleView />} />
        )}
      </div>
    </div>
  );
};

export default ProjectSubmissions;
