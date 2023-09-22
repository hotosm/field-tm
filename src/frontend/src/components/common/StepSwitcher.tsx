import React from 'react';
import AssetModules from '../../shared/AssetModules.js';
import { CommonActions } from '../../store/slices/CommonSlice';
import CoreModules from '../../shared/CoreModules.js';
import { useNavigate } from 'react-router-dom';

const StepSwitcher = ({ data, flag }) => {
  interface IIndividualStep {
    url: string;
    step: number;
    label: string;
    name: string;
  }

  const dispatch = CoreModules.useAppDispatch();
  const navigate = useNavigate();
  const currentStep = CoreModules.useAppSelector((state) => state.common.currentStepFormStep[flag]);

  const toggleStep = (step: IIndividualStep) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step.step }));
    navigate(step.url);
  };
  return (
    <div className="fmtm-flex fmtm-w-fit fmtm-mx-auto fmtm-py-5 fmtm-flex-wrap fmtm-gap-3 fmtm-justify-center">
      {data?.map((step: IIndividualStep, i = 1) => {
        const index = i + 1;
        return (
          <div key={step.step}>
            <div className="fmtm-flex fmtm-items-center">
              <div className="fmtm-flex fmtm-flex-col">
                <div className="fmtm-flex fmtm-items-end fmtm-gap-3">
                  <p className="lg:fmtm-text-xl xl:fmtm-text-2xl fmtm-font-[600] fmtm-ml-1">{step.label}</p>
                  <p className="fmtm-text-lg fmtm-text-gray-500">{step.name}</p>
                </div>
                <div className="fmtm-flex fmtm-items-center">
                  <div
                    className={`lg:fmtm-w-7 lg:fmtm-h-7 xl:fmtm-w-9 xl:fmtm-h-9 fmtm-rounded-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-border-[0.15rem] fmtm-border-primaryRed hover:fmtm-cursor-pointer  ${
                      currentStep.step >= index ? 'fmtm-bg-primaryRed' : 'fmtm-bg-transparent'
                    }`}
                    onClick={() => toggleStep(step)}
                  >
                    <AssetModules.DoneIcon
                      className={`${
                        currentStep.step >= index ? 'fmtm-text-white' : 'fmtm-text-primaryRed'
                      } lg:fmtm-text-lg xl:fmtm-text-xl`}
                    />
                  </div>
                  {data?.length > index && (
                    <div
                      className={`fmtm-border-t-[3px] fmtm-border-primaryRed fmtm-w-[6rem] xl:fmtm-w-[10rem] 2xl:fmtm-w-[12rem] fmtm-mx-4 ${
                        currentStep.step - 1 >= index ? 'fmtm-border-solid' : 'fmtm-border-dashed'
                      }`}
                    ></div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StepSwitcher;
