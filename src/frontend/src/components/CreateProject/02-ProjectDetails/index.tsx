import React from 'react';
import ProjectDetails from './ProjectDetails';
import UploadSurvey from './UploadSurvey';
import MapData from './MapData';

const index = () => {
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <ProjectDetails />
      <hr />
      <UploadSurvey />
      <hr />
      <MapData />
    </div>
  );
};

export default index;
