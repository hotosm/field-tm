import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';

const TasksComponent = ({ qrcode }) => {
  return (
    <div className="fmtm-flex fmtm-justify-center fmtm-py-5 fmtm-border-t-[1px]">
      <div className="fmtm-p-5 fmtm-border-[1px] fmtm-rounded-lg fmtm-relative">
        {qrcode == '' ? (
          <CoreModules.Skeleton width={170} height={170} />
        ) : (
          <img id="qrcodeImg" src={qrcode} alt="qrcode" />
        )}
        <div className="fmtm-rounded-full fmtm-w-10 fmtm-h-10 fmtm-flex fmtm-justify-center fmtm-items-center fmtm-shadow-xl fmtm-absolute fmtm-bottom-0 -fmtm-right-5 fmtm-bg-white ">
          <button
            onClick={() => {
              const downloadLink = document.createElement('a');
              downloadLink.href = qrcode;
              downloadLink.download = `Task_${task}`;
              downloadLink.click();
            }}
            disabled={qrcode == '' ? true : false}
            aria-label="download qrcode"
            className={` ${qrcode === '' ? 'fmtm-cursor-not-allowed fmtm-opacity-50' : 'fmtm-cursor-pointer'}`}
          >
            <AssetModules.FileDownloadIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

export default TasksComponent;
