import React from 'react';

type featureType = {
  title: string;
  description: string;
};

const features: featureType[] = [
  {
    title: 'Flexible Data Collection',
    description:
      'Field-TM offers flexible data collection, supporting diverse survey forms and categories, multiple data types and adaptable workflows to match different field requirements.',
  },
  {
    title: 'Open source and customisable',
    description:
      'Field-TM is open-source and customizable, giving organizations the flexibility to adapt the platform to their unique survey workflows, data needs, and integration requirements.',
  },
  ,
  {
    title: 'Entity level Field Survey Tracking',
    description:
      'Field-TM enables entity-level survey tracking, allowing progress to be monitored and managed for each specific task and overall project in real time.',
  },
];

const Features = () => {
  return (
    <div className="fmtm-px-[3rem] md:fmtm-px-[4.5rem]">
      <h4 className="fmtm-mb-3">MAIN FEATURES</h4>
      <div className="fmtm-grid md:fmtm-grid-cols-3 fmtm-gap-5">
        {features.map((feature, index) => (
          <div key={index} className="fmtm-bg-red-light fmtm-px-5 fmtm-py-5 md:fmtm-py-10 fmtm-rounded-xl">
            <h5 key={index} className="fmtm-mb-2">
              {feature.title}
            </h5>
            <p>{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Features;
