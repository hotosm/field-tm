import React from 'react';
import { motion } from 'motion/react';

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
    <div className="fmtm-px-[2rem] sm:fmtm-px-[3rem] md:fmtm-px-[4.5rem]">
      <motion.h4 className="fmtm-mb-3" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
        Main Features
      </motion.h4>
      <div className="fmtm-grid md:fmtm-grid-cols-3 fmtm-gap-5">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            className="box fmtm-bg-red-light fmtm-px-5 fmtm-py-5 md:fmtm-py-10 fmtm-rounded-xl"
            initial={{ x: -10, y: 0, opacity: 0 }}
            whileInView={{ x: 0, y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ type: 'spring', delay: index * 0.2 }}
          >
            <h5 key={index} className="fmtm-mb-2">
              {feature.title}
            </h5>
            <p>{feature.description}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Features;
