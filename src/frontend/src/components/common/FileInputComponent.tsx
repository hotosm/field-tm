import React, { useRef } from 'react';
import AssetModules from '@/shared/AssetModules.js';

type fileInputComponentType = {
  accept: string;
  customFile: any;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onResetFile: () => void;
  btnText: string;
  fileDescription: string;
  errorMsg: string;
};

const FileInputComponent = ({
  accept = '.geojson, .json',
  customFile,
  onChange,
  onResetFile,
  btnText = 'Select File',
  fileDescription = '*The supported file formats are zipped shapefile, geojson or kml files.',
  errorMsg,
}: fileInputComponentType) => {
  const customFileRef = useRef<any>(null);
  return (
    <div className="fmtm-mt-3 fmtm-pb-3">
      <div className="fmtm-flex fmtm-items-center fmtm-gap-1">
        <label
          id="file-input"
          className="fmtm-bg-primaryRed hover:fmtm-bg-red-900 fmtm-text-white fmtm-px-4 fmtm-py-1 fmtm-rounded-md fmtm-cursor-pointer"
        >
          <p>{btnText}</p>
          <input
            id="data-extract-custom-file"
            ref={customFileRef}
            type="file"
            className="fmtm-hidden"
            onChange={onChange}
            accept={accept}
          />
        </label>
        {customFile && (
          <div className="fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-slate-100 fmtm-duration-300 fmtm-cursor-pointer">
            <AssetModules.ReplayIcon
              className="fmtm-text-gray-600"
              onClick={() => {
                onResetFile();
                customFileRef.current.value = '';
              }}
            />
          </div>
        )}
      </div>
      {errorMsg && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errorMsg}</p>}

      {customFile && (
        <div className="">
          <p>{customFile?.name}</p>
        </div>
      )}
      <p className="fmtm-text-gray-700 fmtm-mt-2">{fileDescription}</p>
    </div>
  );
};

export default FileInputComponent;
