'use client';

import React from 'react';
import * as Progress from '@radix-ui/react-progress';

interface ProgressBarProps {
  currentStep?: number;
  totalSteps?: number;
  currentProgress?: number;
}
const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep, totalSteps }) => {
  const stepProgressInPercent = currentStep && totalSteps ? (currentStep / totalSteps) * 100 : 0;

  return (
    <>
      <p className="fmtm-text-sm">
        {currentStep} out of {totalSteps} tasks
      </p>
      <Progress.Root
        className="fmtm-relative fmtm-overflow-hidden fmtm-bg-red-black fmtm-rounded-full fmtm-w-full fmtm-h-[25px] fmtm-border-2"
        style={{
          // Fix overflow clipping in Safari
          // https://gist.github.com/domske/b66047671c780a238b51c51ffde8d3a0
          transform: 'translateZ(0)',
        }}
        value={stepProgressInPercent.toFixed(2)}
      >
        <Progress.Indicator
          className="fmtm-progress-indicator fmtm-bg-red-500 fmtm-w-full fmtm-h-full fmtm-transition-transform fmtm-duration-[660ms] fmtm-ease-[cubic-bezier(0.65, 0, 0.35, 1)]"
          style={{ transform: `translateX(-${98 - stepProgressInPercent}%)` }}
        >
          <p className="fmtm-absolute fmtm-right-0 fmtm-text-white fmtm-mr-2">{stepProgressInPercent.toFixed(2)}%</p>
        </Progress.Indicator>
      </Progress.Root>
    </>
  );
};

export default ProgressBar;
