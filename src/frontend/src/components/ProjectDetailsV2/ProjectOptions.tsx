import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { DownloadDataExtract, DownloadProjectForm } from '@/api/Project';
import { DownloadProjectSubmission } from '@/api/task';
import Button from '@/components/common/Button';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { GetProjectQrCode } from '@/api/Files';

type projectOptionPropTypes = {
  projectName: string;
};

const ProjectOptions = ({ projectName }: projectOptionPropTypes) => {
  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();

  const downloadProjectFormLoading = useAppSelector((state) => state.project.downloadProjectFormLoading);
  const downloadDataExtractLoading = useAppSelector((state) => state.project.downloadDataExtractLoading);
  const downloadSubmissionLoading = useAppSelector((state) => state.project.downloadSubmissionLoading);

  const projectId: string = params.id;

  const odkToken = useAppSelector((state) => state.project.projectInfo.odk_token);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const { qrcode }: { qrcode: string } = GetProjectQrCode(odkToken, projectName, authDetails?.username);

  const handleDownload = (downloadType: 'form' | 'geojson' | 'extract' | 'submission' | 'qr') => {
    if (downloadType === 'form') {
      dispatch(
        DownloadProjectForm(
          `${import.meta.env.VITE_API_URL}/projects/download-form/${projectId}`,
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
          `${import.meta.env.VITE_API_URL}/projects/features/download?project_id=${projectId}`,
          projectId,
        ),
      );
    } else if (downloadType === 'submission') {
      dispatch(
        DownloadProjectSubmission(`${import.meta.env.VITE_API_URL}/submission/download`, params.name!, {
          project_id: projectId,
          file_type: 'geojson',
          submitted_date_range: null,
        }),
      );
    } else if (downloadType === 'qr') {
      const downloadLink = document.createElement('a');
      downloadLink.href = qrcode;
      downloadLink.download = `Project_${projectId}`;
      downloadLink.click();
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
        <Button
          loadingText="QR CODE"
          btnText="QR CODE"
          btnType="other"
          className={`fmtm-border-red-700 !fmtm-rounded-md fmtm-truncate`}
          icon={<AssetModules.FileDownloadIcon style={{ fontSize: '22px' }} />}
          onClick={(e) => {
            e.stopPropagation();
            handleDownload('qr');
          }}
        />
      </div>
    </>
  );
};

export default ProjectOptions;
