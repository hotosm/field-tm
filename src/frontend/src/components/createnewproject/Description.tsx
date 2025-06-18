import React, { useEffect, useRef } from 'react';
import windowDimention from '@/hooks/WindowDimension';
import { useAppSelector } from '@/types/reduxTypes';

type sectionType = 'Project Details' | 'Project Area' | 'Upload Survey' | 'Map Data' | 'Split Tasks';

type hoveredSectionType = { hoveredSection: string | null };

const scrollOptions: ScrollIntoViewOptions = {
  block: 'nearest',
  inline: 'center',
  behavior: 'smooth',
};

const ProjectDetails = ({ hoveredSection }: hoveredSectionType) => {
  const { windowSize } = windowDimention();
  const tmsRef = useRef<HTMLDivElement>(null);
  const odkRef = useRef<HTMLDivElement>(null);
  const visibilityRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hoveredSection || windowSize.width < 1024) return;
    if (hoveredSection === 'projectdetails-tms') {
      tmsRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'projectdetails-odk') {
      odkRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'projectdetails-visibility') {
      visibilityRef?.current?.scrollIntoView(scrollOptions);
    }
  }, [hoveredSection]);

  return (
    <div
      className={`${hoveredSection ? 'fmtm-text-gray-400' : 'fmtm-text-gray-500'} lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3 fmtm-duration-150`}
    >
      <span>
        Fill in your project basic information such as name, description, hashtag, etc. This captures essential
        information about your project.
      </span>
      <div
        ref={odkRef}
        className={`${hoveredSection === 'projectdetails-odk' && 'fmtm-text-gray-800'} fmtm-duration-150 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
      >
        <span>To complete the first step, you will need the login credentials of ODK Central Server.</span>{' '}
        <span>
          <a
            href="https://docs.getodk.org/central-install-digital-ocean/"
            className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
            target="_"
          >
            Here{' '}
          </a>
          <span>
            are the instructions for setting up a Central ODK Server on Digital Ocean, if you haven’t already.
          </span>
        </span>
      </div>
      <div
        ref={tmsRef}
        className={`${hoveredSection === 'projectdetails-tms' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        You can use the &apos; Custom TMS URL&apos; option to integrate high-resolution aerial imagery like
        OpenAerialMap{' '}
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
      </div>
      <div
        ref={visibilityRef}
        className={`${hoveredSection === 'projectdetails-visibility' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        You can choose the visibility of your project. A <span className="fmtm-font-semibold">public project</span> is
        accessible to everyone, while a <span className="fmtm-font-semibold">private project</span> is only accessible
        to invited users and admins.
      </div>
    </div>
  );
};

const UploadArea = ({ hoveredSection }: hoveredSectionType) => {
  const { windowSize } = windowDimention();
  const drawRef = useRef<HTMLDivElement>(null);
  const uploadRef = useRef<HTMLDivElement>(null);
  const uploadGeojsonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hoveredSection || windowSize.width < 1024) return;
    if (hoveredSection === 'uploadarea-draw') {
      drawRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'uploadarea-upload_file') {
      uploadRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'uploadarea-uploadgeojson') {
      uploadGeojsonRef?.current?.scrollIntoView(scrollOptions);
    }
  }, [hoveredSection]);

  return (
    <div
      className={`${hoveredSection ? 'fmtm-text-gray-400' : 'fmtm-text-gray-500'} lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
    >
      <div
        ref={drawRef}
        className={`${hoveredSection === 'uploadarea-draw' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        <p>You can draw a freehand polygon on map interface.</p> <p>Click on the reset button to redraw the AOI.</p>
      </div>
      <div
        ref={uploadRef}
        className={`${hoveredSection === 'uploadarea-upload_file' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        <p>You may also choose to upload the AOI. Note: The file upload only supports .geojson format. </p>
      </div>
      <span>The total area of the AOI is also calculated and displayed on the screen.</span>
      <p
        ref={uploadGeojsonRef}
        className={`${hoveredSection === 'uploadarea-uploadgeojson' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        <b>Note:</b> The uploaded geojson should be in EPSG:4326 coordinate system.
      </p>
    </div>
  );
};

const UploadSurvey = ({ hoveredSection }: hoveredSectionType) => {
  const { windowSize } = windowDimention();
  const uploadFormRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hoveredSection || windowSize.width < 1024) return;
    if (hoveredSection === 'selectform-selectform') {
      uploadFormRef?.current?.scrollIntoView(scrollOptions);
    }
  }, [hoveredSection]);

  return (
    <div
      className={`${hoveredSection ? 'fmtm-text-gray-400' : 'fmtm-text-gray-500'} lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
    >
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
      <p
        ref={uploadFormRef}
        className={`${hoveredSection === 'selectform-selectform' && 'fmtm-text-gray-800'} fmtm-duration-150 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
      >
        <span>
          <b>Note:</b> Uploading a custom form may make uploading of the final dataset to OSM difficult.
        </span>
        <span>
          <b>Note:</b> Additional questions will be incorporated into your custom form to assess the digitization
          status.
        </span>
      </p>
    </div>
  );
};

const MapFeature = ({ hoveredSection }: hoveredSectionType) => {
  const { windowSize } = windowDimention();
  const osmFeaturesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hoveredSection || windowSize.width < 1024) return;
    if (hoveredSection === 'mapfeatures-osm') {
      osmFeaturesRef?.current?.scrollIntoView(scrollOptions);
    }
  }, [hoveredSection]);

  return (
    <div
      className={`${hoveredSection ? 'fmtm-text-gray-400' : 'fmtm-text-gray-500'} lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
    >
      <span>You may either choose to use OSM data, or upload your own data for the mapping project.</span>
      <div
        ref={osmFeaturesRef}
        className={`${hoveredSection === 'mapfeatures-osm' && 'fmtm-text-gray-800'} fmtm-duration-150 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
      >
        <span>The relevant map data that exist on OSM are imported based on the select map area.</span>{' '}
        <span>
          You can use these map data to use the &apos;select from map&apos; functionality from ODK that allows you to
          select the feature to collect data for.
        </span>{' '}
      </div>
    </div>
  );
};

const SplitTasks = ({ hoveredSection }: hoveredSectionType) => {
  const { windowSize } = windowDimention();
  const divdeOnSquareRef = useRef<HTMLDivElement>(null);
  const chooseAreaRef = useRef<HTMLDivElement>(null);
  const taskSplitRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hoveredSection || windowSize.width < 1024) return;
    if (hoveredSection === 'splittasks-DIVIDE_ON_SQUARE') {
      divdeOnSquareRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'splittasks-CHOOSE_AREA_AS_TASK') {
      chooseAreaRef?.current?.scrollIntoView(scrollOptions);
    }
    if (hoveredSection === 'splittasks-TASK_SPLITTING_ALGORITHM') {
      taskSplitRef?.current?.scrollIntoView(scrollOptions);
    }
  }, [hoveredSection]);

  return (
    <div
      className={`${hoveredSection ? 'fmtm-text-gray-400' : 'fmtm-text-gray-500'} lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3`}
    >
      <span>You may choose how to divide an area into tasks for field mapping</span>
      <span
        ref={divdeOnSquareRef}
        className={`${hoveredSection === 'splittasks-DIVIDE_ON_SQUARE' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        Divide area on squares split the AOI into squares based on user’s input in dimensions
      </span>
      <span
        ref={chooseAreaRef}
        className={`${hoveredSection === 'splittasks-CHOOSE_AREA_AS_TASK' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        Choose area as task creates the number of tasks based on number of polygons in AOI
      </span>
      <span
        ref={taskSplitRef}
        className={`${hoveredSection === 'splittasks-TASK_SPLITTING_ALGORITHM' && 'fmtm-text-gray-800'} fmtm-duration-150`}
      >
        Task splitting algorithm splits an entire AOI into smallers tasks based on linear networks (road, river)
        followed by taking into account the input of number of average buildings per task
      </span>
    </div>
  );
};

const getDescription = (section: sectionType, hoveredSection: string | null): React.JSX.Element => {
  switch (section) {
    case 'Project Details':
      return <ProjectDetails hoveredSection={hoveredSection} />;
    case 'Project Area':
      return <UploadArea hoveredSection={hoveredSection} />;
    case 'Upload Survey':
      return <UploadSurvey hoveredSection={hoveredSection} />;
    case 'Map Data':
      return <MapFeature hoveredSection={hoveredSection} />;
    case 'Split Tasks':
      return <SplitTasks hoveredSection={hoveredSection} />;
    default:
      return <></>;
  }
};

const Description = ({ section }: { section: sectionType }) => {
  const descriptionToFocus = useAppSelector((state) => state.createproject.descriptionToFocus);

  return (
    <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6 lg:fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
      <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">{section}</h6>
      {getDescription(section, descriptionToFocus)}
    </div>
  );
};

export default Description;
