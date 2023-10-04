import React, { useRef, useState } from 'react';
import AssetModules from '../../shared/AssetModules.js';

const FileInputComponent = ({ customFileRef, customFormFile, onChange, onResetFile }) => {
  const changeFileHandler = (event) => {
    // handle file change logic here
  };

  const resetFile = () => {
    // reset file logic here
  };

  return (
    <div className="fmtm-mt-6 fmtm-pb-3">
      <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
        <label
          id="file-input"
          className="fmtm-bg-primaryRed fmtm-text-white fmtm-px-4 fmtm-py-1 fmtm-rounded-md fmtm-cursor-pointer"
        >
          <p>Select a Building file</p>
          <input
            id="data-extract-custom-file"
            ref={customFileRef}
            type="file"
            className="fmtm-hidden"
            onChange={onChange}
            accept=".geojson, .json"
          />
        </label>
        <div className="fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-slate-100 fmtm-duration-300 fmtm-cursor-pointer">
          <AssetModules.ReplayIcon className="fmtm-text-gray-600" onClick={onResetFile} />
        </div>
      </div>
      {customFormFile && (
        <div className="fmtm-mt-2">
          <p>{customFormFile?.name}</p>
        </div>
      )}
      <p className="fmtm-text-gray-700 fmtm-mt-10">
        *The supported file formats are zipped shapefile, geojson or kml files.
      </p>
    </div>
  );
};

export default FileInputComponent;
