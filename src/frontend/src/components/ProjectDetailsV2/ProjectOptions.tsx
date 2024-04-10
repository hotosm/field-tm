import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { DownloadDataExtract, DownloadProjectForm } from '@/api/Project';
import Button from '@/components/common/Button';
import { downloadProjectFormLoadingType } from '@/models/project/projectModel';

const ProjectOptions = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();

  const downloadProjectFormLoading: downloadProjectFormLoadingType = CoreModules.useAppSelector(
    (state) => state.project.downloadProjectFormLoading,
  );
  const downloadDataExtractLoading: boolean = CoreModules.useAppSelector(
    (state) => state.project.downloadDataExtractLoading,
  );

  const projectId: string = params.id;

  const handleDownload = (downloadType) => {
    if (downloadType === 'form') {
      dispatch(
        DownloadProjectForm(
          `${import.meta.env.VITE_API_URL}/projects/download-form/${projectId}/`,
          downloadType,
          projectId,
        ),
      );
    } else if (downloadType === 'geojson') {
      dispatch(
        DownloadProjectForm(
          `${import.meta.env.VITE_API_URL}/projects/${projectId}/download_tasks`,
          downloadType,
          projectId,
        ),
      );
    }
  };
  const onDataExtractDownload = () => {
    dispatch(
      DownloadDataExtract(`${import.meta.env.VITE_API_URL}/projects/features/download/?project_id=${projectId}`),
    );
  };
  return (
    <>
      <div className="fmtm-flex fmtm-gap-4 fmtm-flex-col md:fmtm-flex-row">
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
