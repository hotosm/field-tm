import React, { useState } from 'react';
// import AssignTab from './Assign';
import InviteTab from './Invite';
import { project_roles } from '@/types/enums';

const tabList: ['Invite'] = ['Invite'];
{
  /* TODO: work on user task assignment after finalization */
}
// const tabList: ['Assign', 'Invite'] = ['Assign', 'Invite'];

const roleList = [
  {
    id: 'MAPPER',
    label: 'Mapper',
    value: project_roles.MAPPER,
  },
  {
    id: 'PROJECT_ADMIN',
    label: 'Project Admin',
    value: project_roles.PROJECT_ADMIN,
  },
];

const UserTab = () => {
  const [tabView, setTabView] = useState<'Assign' | 'Invite'>('Invite');

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-w-full fmtm-h-full">
      <div className="fmtm-flex fmtm-gap-3 fmtm-mb-2">
        {tabList.map((tab) => (
          <div
            key={tab}
            className={`fmtm-button fmtm-w-fit fmtm-text-grey-900 fmtm-px-2 fmtm-border-b-[1px] hover:fmtm-border-red-medium fmtm-duration-300 fmtm-cursor-pointer ${
              tabView === tab ? 'fmtm-border-red-medium' : 'fmtm-border-transparent'
            }`}
            onClick={() => setTabView(tab)}
          >
            {tab}
          </div>
        ))}
      </div>
      <InviteTab roleList={roleList} />
      {/* TODO: work on user task assignment after finalization */}
      {/* {tabView === 'Assign' ? <AssignTab roleList={roleList} /> : <InviteTab roleList={roleList} />} */}
    </div>
  );
};

export default UserTab;
