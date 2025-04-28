import React from 'react';

const InstructionsSidebar = () => {
  return (
    <div className="lg:fmtm-w-[30%] xl:fmtm-w-[23rem] fmtm-bg-white fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 fmtm-h-fit">
      <h5 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7">Request for the organization creation</h5>
      <p className="fmtm-text-[#7A7676] fmtm-flex fmtm-flex-col fmtm-gap-3 lg:fmtm-gap-5">
        <span>
          Project creation and other advanced usage of the HOT Field Tasking Manager needs an organisation to be
          created.
        </span>
        <span>
          HOT reserves all rights to give, and remove, all roles and permissions on Field-TM as well as alter or remove
          projects as deemed necessary.
        </span>
        <span>
          Your input will be collected, stored, and processed by the Humanitarian OpenStreetMap Team (HOT) for the
          purpose of evaluating your application and hosting your organization’s presence. Factual data about your use
          of the Tasking Manager may be published for HOT to promote and demonstrate use of the Field-TM.{' '}
        </span>
        <span>Please make sure the information you are providing are correct.</span>
      </p>
    </div>
  );
};

export default InstructionsSidebar;
