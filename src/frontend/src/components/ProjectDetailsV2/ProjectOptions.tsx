import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { DownloadDataExtract, DownloadProjectForm, DownloadSubmissionGeojson } from '@/api/Project';
import Button from '@/components/common/Button';
import { useAppSelector } from '@/types/reduxTypes';

type projectOptionPropTypes = {
  projectName: string;
};

const ProjectOptions = ({ projectName }: projectOptionPropTypes) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();

  const downloadProjectFormLoading = useAppSelector((state) => state.project.downloadProjectFormLoading);
  const downloadDataExtractLoading = useAppSelector((state) => state.project.downloadDataExtractLoading);
  const downloadSubmissionLoading = useAppSelector((state) => state.project.downloadSubmissionLoading);

  const projectId: string = params.id;

  const handleDownload = (downloadType: 'form' | 'geojson' | 'extract' | 'submission') => {
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
    } else if (downloadType === 'extract') {
      dispatch(
        DownloadDataExtract(
          `${import.meta.env.VITE_API_URL}/projects/features/download/?project_id=${projectId}`,
          projectId,
        ),
      );
    } else if (downloadType === 'submission') {
      dispatch(
        DownloadSubmissionGeojson(
          `${import.meta.env.VITE_API_URL}/submission/download-submission-geojson?project_id=${projectId}`,
          projectName,
        ),
      );
    }
  };

  return (
    <>
      <div className="fmtm-flex fmtm-gap-4 fmtm-flex-col lg:fmtm-flex-row">
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
          loadingText="MAP FEATURES"
          btnText="MAP FEATURES"
          btnType="other"
          className={`${
            downloadDataExtractLoading ? '' : 'hover:fmtm-text-red-700'
          } fmtm-border-red-700 !fmtm-rounded-md fmtm-truncate`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            handleDownload('extract');
          }}
        />
        <Button
          isLoading={downloadSubmissionLoading}
          loadingText="SUBMISSIONS"
          btnText="SUBMISSIONS"
          btnType="other"
          className={`${
            downloadSubmissionLoading ? '' : 'hover:fmtm-text-red-700'
          } fmtm-border-red-700 !fmtm-rounded-md fmtm-truncate`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            handleDownload('submission');
          }}
        />
      </div>
    </>
  );
};

export default ProjectOptions;
