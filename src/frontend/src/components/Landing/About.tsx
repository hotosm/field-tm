import React from 'react';
import MappingImg from '@/assets/images/landing-pic-1.jpg';

const About = () => {
  return (
    <div className="fmtm-w-full fmtm-grid md:fmtm-grid-cols-2 fmtm-items-center fmtm-px-[2rem] sm:fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-gap-10">
      <div>
        <h2 className="fmtm-mb-4 fmtm-text-[1.625rem] md:fmtm-text-[2.375rem]">What is it?</h2>
        <p className="fmtm-text-justify fmtm-mb-2">
          The Field Tasking Manager (Field-TM) helps teams add local knowledge to map features by coordinating mapping
          in the field.
        </p>
        <p className="fmtm-text-justify">
          Field-TM facilitates collaborative mapping by supporting and extending existing mature tools. The Field-TM is
          a standalone mobile and web application that works using OpenDataKit (ODK), a powerful data collection
          platform that leverages commonly-available mobile Android devices to enable people to input information,
          including geospatial data in the field.
        </p>
      </div>
      <div>
        <img
          src={MappingImg}
          className="fmtm-mx-auto fmtm-rounded-2xl"
          alt="A project manager who has just created an FieldTM project on their laptop demonstrates to a field mapper how they can select their assigned buildings on their phone"
        />
      </div>
    </div>
  );
};

export default About;
