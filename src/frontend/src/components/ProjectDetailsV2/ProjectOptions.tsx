import React, { useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import environment from '@/environment';
import { DownloadDataExtract, DownloadProjectForm } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';

const ProjectOptions = ({ setToggleGenerateModal }) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();

  const downloadProjectFormLoading = CoreModules.useAppSelector((state) => state.project.downloadProjectFormLoading);
  const downloadDataExtractLoading = CoreModules.useAppSelector((state) => state.project.downloadDataExtractLoading);

  const encodedId = params.id;
  const decodedId = environment.decode(encodedId);

  const handleDownload = (downloadType) => {
    if (downloadType === 'form') {
      dispatch(
        DownloadProjectForm(
          `${import.meta.env.VITE_API_URL}/projects/download_form/${decodedId}/`,
          downloadType,
          decodedId,
        ),
      );
    } else if (downloadType === 'geojson') {
      dispatch(
        DownloadProjectForm(
          `${import.meta.env.VITE_API_URL}/projects/${decodedId}/download_tasks`,
          downloadType,
          decodedId,
        ),
      );
    }
  };
  const onDataExtractDownload = () => {
    dispatch(
      DownloadDataExtract(`${import.meta.env.VITE_API_URL}/projects/features/download/?project_id=${decodedId}`),
    );
  };
  return (
    <>
      <div className="sm:fmtm-hidden">
        <div className="fmtm-flex fmtm-gap-3 fmtm-border-b-[1px] fmtm-pb-2 fmtm-mb-4 sm:fmtm-hidden">
          <AssetModules.ListViewIcon className=" fmtm-text-primaryRed" sx={{ fontSize: '35px' }} />
          <p className="fmtm-text-2xl">Project Options</p>
        </div>
        <div
          className={`fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-6 lg:fmtm-gap-0 fmtm-px-3 sm:fmtm-px-0 sm:fmtm-flex`}
        >
          <div className="fmtm-w-full fmtm-flex fmtm-flex-col fmtm-items-start sm:fmtm-flex-row  sm:fmtm-justify-center lg:fmtm-justify-start sm:fmtm-items-center fmtm-gap-6  sm:fmtm-ml-4">
            <CoreModules.LoadingButton
              onClick={() => handleDownload('form')}
              sx={{ width: 'unset' }}
              loading={downloadProjectFormLoading.type === 'form' && downloadProjectFormLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              Form
            </CoreModules.LoadingButton>
            <CoreModules.LoadingButton
              onClick={() => handleDownload('geojson')}
              sx={{ width: 'unset' }}
              loading={downloadProjectFormLoading.type === 'geojson' && downloadProjectFormLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              Tasks
            </CoreModules.LoadingButton>
            <CoreModules.LoadingButton
              onClick={() => onDataExtractDownload()}
              sx={{ width: 'unset' }}
              loading={downloadDataExtractLoading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
              className="fmtm-truncate"
            >
              Data Extract
            </CoreModules.LoadingButton>
          </div>
          <div className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row sm:fmtm-justify-center lg:fmtm-justify-end fmtm-w-full sm:fmtm-ml-4 fmtm-gap-6">
            <CoreModules.Link
              to={`/projectInfo/${encodedId}`}
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'flex-end',
                textDecoration: 'none',
                marginRight: '15px',
              }}
              className="fmtm-w-fit"
            >
              <CoreModules.Button variant="contained" color="error">
                ProjectInfo
              </CoreModules.Button>
            </CoreModules.Link>
            <CoreModules.Button
              onClick={() => {
                setToggleGenerateModal(true);
                dispatch(ProjectActions.SetMobileFooterSelection('explore'));
              }}
              variant="contained"
              color="error"
              sx={{ width: '200px', mr: '15px' }}
              endIcon={<AssetModules.BoltIcon />}
              className="fmtm-truncate"
            >
              Generate MbTiles
            </CoreModules.Button>
            <CoreModules.Button
              onClick={() => navigate(`/manage-project/${encodedId}`)}
              variant="contained"
              color="error"
              sx={{ width: '200px', mr: '15px' }}
              endIcon={<AssetModules.SettingsIcon />}
              className="fmtm-truncate"
            >
              Manage Project
            </CoreModules.Button>
            <CoreModules.Button
              onClick={() => navigate(`/project-submissions/${encodedId}`)}
              variant="contained"
              color="error"
              sx={{ width: '200px', mr: '15px' }}
              className="fmtm-truncate"
            >
              View Infographics
            </CoreModules.Button>
          </div>
        </div>
      </div>
      <div className="fmtm-hidden sm:fmtm-flex fmtm-gap-4 fmtm-flex-col md:fmtm-flex-row">
        <Button
          isLoading={downloadProjectFormLoading.type === 'form' && downloadProjectFormLoading.loading}
          loadingText="FORM"
          btnText="FORM"
          btnType="other"
          className={`${
            downloadProjectFormLoading.type === 'form' && downloadProjectFormLoading.loading
              ? ''
              : 'hover:fmtm-text-red-700'
          } fmtm-border-red-700 !fmtm-rounded-md`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            handleDownload('form');
          }}
        />
        <Button
          isLoading={downloadProjectFormLoading.type === 'geojson' && downloadProjectFormLoading.loading}
          loadingText="TASKS"
          btnText="TASKS"
          btnType="other"
          className={`${
            downloadProjectFormLoading.type === 'geojson' && downloadProjectFormLoading.loading
              ? ''
              : 'hover:fmtm-text-red-700'
          } fmtm-border-red-700 !fmtm-rounded-md`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            handleDownload('geojson');
          }}
        />
        <Button
          isLoading={downloadDataExtractLoading}
          loadingText="DATA EXTRACT"
          btnText="DATA EXTRACT"
          btnType="other"
          className={`${
            downloadDataExtractLoading ? '' : 'hover:fmtm-text-red-700'
          } fmtm-border-red-700 !fmtm-rounded-md fmtm-truncate`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            onDataExtractDownload();
          }}
        />
      </div>
    </>
  );
};

export default ProjectOptions;
