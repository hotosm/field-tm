import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { DownloadDataExtract, DownloadProjectForm } from '@/api/Project';
import { DownloadProjectSubmission } from '@/api/task';
import Button from '@/components/common/Button';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { GetProjectQrCode } from '@/api/Files';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type downloadTypeType = 'form' | 'geojson' | 'extract' | 'submission' | 'qr';
type downloadButtonType = { downloadType: downloadTypeType; label: string; isLoading: boolean; show: boolean };

const ProjectOptions = () => {
  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();

  const downloadProjectFormLoading = useAppSelector((state) => state.project.downloadProjectFormLoading);
  const downloadDataExtractLoading = useAppSelector((state) => state.project.downloadDataExtractLoading);
  const downloadSubmissionLoading = useAppSelector((state) => state.task.downloadSubmissionLoading);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);

  const downloadButtonList: downloadButtonType[] = [
    {
      downloadType: 'form',
      label: 'FORM',
      isLoading: downloadProjectFormLoading.type === 'form' && downloadProjectFormLoading.loading,
      show: true,
    },
    {
      downloadType: 'geojson',
      label: 'TASKS',
      isLoading: downloadProjectFormLoading.type === 'geojson' && downloadProjectFormLoading.loading,
      show: true,
    },
    { downloadType: 'extract', label: 'MAP FEATURES', isLoading: downloadDataExtractLoading, show: true },
    {
      downloadType: 'submission',
      label: 'SUBMISSIONS',
      isLoading: downloadSubmissionLoading.fileType === 'geojson' && downloadSubmissionLoading.loading,
      show: true,
    },
    { downloadType: 'qr', label: 'QR CODE', isLoading: false, show: projectInfo.use_odk_collect || false },
  ];

  const projectId: string = params.id;

  const odkToken = useAppSelector((state) => state.project.projectInfo.odk_token);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const { qrcode }: { qrcode: string } = GetProjectQrCode(odkToken, projectInfo.name, authDetails?.username);

  const handleDownload = (downloadType: downloadTypeType) => {
    switch (downloadType) {
      case 'form':
        dispatch(
          DownloadProjectForm(`${VITE_API_URL}/central/download-form?project_id=${projectId}`, downloadType, projectId),
        );
        break;
      case 'geojson':
        dispatch(DownloadProjectForm(`${VITE_API_URL}/projects/${projectId}/download_tasks`, downloadType, projectId));
        break;
      case 'extract':
        dispatch(DownloadDataExtract(`${VITE_API_URL}/projects/features/download?project_id=${projectId}`, projectId));
        break;
      case 'submission':
        dispatch(
          DownloadProjectSubmission(`${VITE_API_URL}/submission/download`, projectInfo.name as string, {
            project_id: projectId,
            file_type: 'geojson',
            submitted_date_range: null,
          }),
        );
        break;
      case 'qr':
        const downloadLink = document.createElement('a');
        downloadLink.href = qrcode;
        downloadLink.download = `Project_${projectId}.png`;
        downloadLink.click();
        break;
    }
  };

  return (
    <div className="fmtm-flex fmtm-gap-2 fmtm-flex-col">
      {downloadButtonList.map(
        (btn) =>
          btn.show && (
            <Button
              key={btn.downloadType}
              variant="secondary-grey"
              onClick={() => handleDownload(btn.downloadType)}
              isLoading={btn.isLoading}
            >
              {btn.label}
              <AssetModules.FileDownloadIcon style={{ fontSize: '20px' }} />
            </Button>
          ),
      )}
    </div>
  );
};

export default ProjectOptions;
