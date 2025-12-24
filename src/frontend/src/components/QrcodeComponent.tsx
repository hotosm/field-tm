import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { useAppSelector } from '@/types/reduxTypes';
import { GetProjectQrCode } from '@/api/Files';

type tasksComponentType = {
  projectId?: string;
};

const QrcodeComponent = ({ projectId }: tasksComponentType) => {
  const downloadQR = () => {
    const downloadLink = document.createElement('a');
    downloadLink.href = qrcode;
    downloadLink.download = `Project_${projectId}`;
    downloadLink.click();
  };

  const projectName = useAppSelector((state) => state.project.projectInfo.project_name);
  const odkToken = useAppSelector((state) => state.project.projectInfo.odk_token);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  const { qrcode }: { qrcode: string } = GetProjectQrCode(odkToken, projectName, authDetails?.username);

  return (
    <div className="fmtm-flex fmtm-justify-center sm:fmtm-py-5 fmtm-border-t-[1px]">
      <div className="fmtm-relative fmtm-hidden sm:fmtm-block fmtm-bg-white fmtm-p-2 !fmtm-w-[9rem] fmtm-rounded-tl-lg fmtm-rounded-bl-lg">
        {qrcode == '' ? (
          <CoreModules.Skeleton width={128} height={128} />
        ) : (
          <img id="qrcodeImg" src={qrcode} alt="qrcode" className="" />
        )}
        <p className="fmtm-text-center fmtm-leading-4 fmtm-text-sm fmtm-mt-2">Scan to load project on ODK</p>
      </div>
      <div className="fmtm-block sm:fmtm-hidden">
        <button
          className={`fmtm-border-primaryRed fmtm-border-[1px] fmtm-text-primaryRed fmtm-px-2 fmtm-py-1 fmtm-rounded fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-my-2 hover:fmtm-bg-red-50 ${
            qrcode == '' ? 'fmtm-cursor-not-allowed fmtm-opacity-50' : 'fmtm-cursor-pointer'
          }`}
          aria-label="download qrcode"
          disabled={!qrcode}
          onClick={downloadQR}
        >
          <AssetModules.FileDownloadOutlinedIcon />
          <p>Download QR</p>
          <AssetModules.QrCode2OutlinedIcon />
        </button>
      </div>
    </div>
  );
};

export default QrcodeComponent;
