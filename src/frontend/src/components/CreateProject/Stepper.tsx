import React from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { createProjectSteps } from './constants';

type propType = {
  step: number;
  toggleStep: (step: number) => void;
  canSwitchSteps?: boolean;
};

type IndividualStepType = {
  step: number;
  label: string;
  name: string;
};

const Stepper = ({ step, toggleStep, canSwitchSteps }: propType) => {
  return (
    <div className="fmtm-flex lg:fmtm-flex-col fmtm-justify-around fmtm-flex-wrap lg:fmtm-justify-start fmtm-py-5 fmtm-px-6 fmtm-gap-4 sm:fmtm-gap-7">
      {createProjectSteps?.map((stepData: IndividualStepType, i = 1) => {
        const index = i + 1;
        return (
          <div key={stepData.step} className="fmtm-flex fmtm-items-center fmtm-gap-x-2">
            <div
              className={`${step === index && 'currentstep-pointer'} ${index < step ? 'fmtm-bg-grey-800 fmtm-border-grey-800' : index > step ? 'fmtm-border-grey-700' : 'fmtm-border-primaryRed'} fmtm-w-7 fmtm-h-7 fmtm-rounded-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-border-2`}
              onClick={() => {
                if (canSwitchSteps) toggleStep(step);
              }}
            >
              {step > index ? (
                <AssetModules.DoneIcon className="fmtm-text-white !fmtm-text-base" />
              ) : (
                <p
                  className={`fmtm-text-sm fmtm-font-semibold ${index === step ? 'fmtm-text-primaryRed' : 'fmtm-text-grey-700'}`}
                >
                  {stepData.label}
                </p>
              )}
            </div>
            <p className={`${index === step ? 'fmtm-body-md-semibold' : 'fmtm-body-md'} fmtm-text-grey-700`}>
              {stepData.name}
            </p>
          </div>
        );
      })}
    </div>
  );
};

export default Stepper;
