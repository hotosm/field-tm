import React from 'react';
import { z } from 'zod/v4';
import { useFormContext } from 'react-hook-form';
import { createProjectValidationSchema } from './validation';
import Button from '@/components/common/Button';

import QfieldLogo from '@/assets/images/qfield-logo.svg';
import OdkLogo from '@/assets/images/odk-logo.svg';
import { field_mapping_app } from '@/types/enums';
import { useSearchParams } from 'react-router-dom';

const mappingApps = [
  {
    id: field_mapping_app.QField,
    title: 'QField',
    description: 'The QField mobile application (offline-capable)',
    logo: QfieldLogo,
  },
  {
    id: field_mapping_app.ODK,
    title: 'ODK',
    description: 'The ODK Collect mobile application (offline-capable)',
    logo: OdkLogo,
  },
];

const ProjectTypeSelector = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { setValue } = form;

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-justify-center fmtm-h-full fmtm-bg-white fmtm-rounded-xl">
      <div className="fmtm-text-center fmtm-mb-8">
        <h2 className="fmtm-text-2xl fmtm-font-bold fmtm-text-gray-800 fmtm-mb-4">
          Choose Your Field Mapping Application
        </h2>
        <p className="fmtm-text-gray-600">Select the application you would like to use for field data collection</p>
      </div>

      <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-3 fmtm-gap-6 fmtm-w-full fmtm-max-w-4xl fmtm-mb-20">
        {mappingApps.map((app) => (
          <div
            key={app.id}
            className="fmtm-bg-gray-50 fmtm-border fmtm-border-gray-200 fmtm-rounded-lg fmtm-p-6 fmtm-text-center fmtm-transition-all fmtm-duration-200 hover:fmtm-bg-gray-100 hover:fmtm-shadow-md fmtm-flex fmtm-flex-col fmtm-min-h-[200px]"
          >
            <div className="fmtm-flex fmtm-justify-center fmtm-mb-4">
              <img src={app.logo} alt={`${app.title} logo`} className="fmtm-w-12 fmtm-h-12 fmtm-object-contain" />
            </div>
            <h3 className="fmtm-text-lg fmtm-font-semibold fmtm-text-gray-800 fmtm-mb-2">{app.title}</h3>
            <p className="fmtm-text-sm fmtm-text-gray-600 fmtm-mb-6 fmtm-flex-grow">{app.description}</p>
            <Button
              variant="primary-grey"
              onClick={() => {
                setValue('field_mapping_app', app.id);
                setSearchParams({ step: '1' });
              }}
              className="fmtm-w-full fmtm-mt-auto"
            >
              Select {app.title}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectTypeSelector;
