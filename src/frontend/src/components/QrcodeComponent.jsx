import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';

const TasksComponent = ({ qrcode, taskId }) => {
  const downloadQR = () => {
    const downloadLink = document.createElement('a');
    downloadLink.href = qrcode;
    downloadLink.download = `Task_${taskId}`;
    downloadLink.click();
  };
  return (
    <div className="fmtm-flex fmtm-justify-center sm:fmtm-py-5 fmtm-border-t-[1px]">
      <div className="fmtm-p-5 fmtm-border-[1px] fmtm-rounded-lg fmtm-relative fmtm-hidden sm:fmtm-block">
        {qrcode == '' ? (
          <CoreModules.Skeleton width={170} height={170} />
        ) : (
          <img id="qrcodeImg" src={qrcode} alt="qrcode" />
        )}
        <div className="fmtm-rounded-full fmtm-w-10 fmtm-h-10 fmtm-flex fmtm-justify-center fmtm-items-center fmtm-shadow-xl fmtm-absolute fmtm-bottom-0 -fmtm-right-5 fmtm-bg-white ">
          <button
            onClick={downloadQR}
            disabled={qrcode == '' ? true : false}
            aria-label="download qrcode"
            className={` ${qrcode === '' ? 'fmtm-cursor-not-allowed fmtm-opacity-50' : 'fmtm-cursor-pointer'}`}
            title="Download QR Code"
          >
            <AssetModules.FileDownloadIcon />
          </button>
        </div>
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

export default TasksComponent;
