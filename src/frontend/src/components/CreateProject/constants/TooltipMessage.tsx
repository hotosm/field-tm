import React from 'react';

const ProjectArea = () => (
  <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
    <div>
      <p>Draw:</p>
      <p>You can draw a freehand polygon on map interface.</p> <p>Click on the reset button to redraw the AOI.</p>
    </div>
    <div>
      <p>Upload:</p>
      <p>You may also choose to upload the AOI. Note: The file upload only supports .geojson format. </p>
    </div>
    <p>The total area of the AOI is also calculated and displayed on the screen.</p>
    <p>
      <b>Note:</b> The uploaded geojson should be in EPSG:4326 coordinate system.
    </p>
  </div>
);

const ProjectType = () => (
  <span>
    You can choose the visibility of your project. A <span className="fmtm-font-semibold">public project</span> is
    accessible to everyone, while a <span className="fmtm-font-semibold">private project</span> is only accessible to
    invited users and admins.
  </span>
);

const TMSBasemap = () => (
  <span>
    You can use the &apos; Custom TMS URL&apos; option to integrate high-resolution aerial imagery like OpenAerialMap{' '}
    <a
      href="https://openaerialmap.org/"
      className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
      target="_"
    >
      (OAM)
    </a>
    . Simply obtain the TMS URL and paste it into the custom TMS field. More details:{' '}
    <a
      href="https://docs.openaerialmap.org/"
      className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
      target="_"
    >
      OpenAerialMap Documentation
    </a>
    .
  </span>
);

const UploadForm = () => (
  <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
    <span>
      You may choose to upload a pre-configured XLSForm, or an entirely custom form. Click{' '}
      <a
        href="https://hotosm.github.io/osm-fieldwork/about/xlsforms/"
        target="_"
        className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer"
      >
        here
      </a>{' '}
      to learn more about XLSForm building.{' '}
    </span>

    <p>
      <b>Note:</b> Uploading a custom form may make uploading of the final dataset to OSM difficult.
    </p>
    <p>
      <b>Note:</b> Additional questions will be incorporated into your custom form to assess the digitization status.
    </p>
  </div>
);

const UploadMapData = () => (
  <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
    <p>You may either choose to use OSM data, or upload your own data for the mapping project.</p>
    <div>
      <p>The relevant map data that exist on OSM are imported based on the select map area.</p>
      <p>
        You can use these map data to use the &apos;select from map&apos; functionality from ODK that allows you to
        select the feature to collect data for.
      </p>
    </div>
  </div>
);

const SplitOption = () => (
  <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
    <p>You may choose how to divide an area into tasks for field mapping:</p>
    <p>i) Divide area on squares split the AOI into squares based on user’s input in dimensions</p>
    <p>ii) Choose area as task creates the number of tasks based on number of polygons in AOI</p>
    <p>
      iii) Task splitting algorithm splits an entire AOI into smallers tasks based on linear networks (road, river)
      followed by taking into account the input of number of average buildings per task
    </p>
  </div>
);

export const TooltipMessage = ({ name }) => {
  switch (name) {
    case 'ProjectArea':
      return <ProjectArea />;
    case 'ProjectType':
      return <ProjectType />;
    case 'TMSBasemap':
      return <TMSBasemap />;
    case 'UploadForm':
      return <UploadForm />;
    case 'UploadMapData':
      return <UploadMapData />;
    case 'SplitOption':
      return <SplitOption />;
    default:
      return null;
  }
};
