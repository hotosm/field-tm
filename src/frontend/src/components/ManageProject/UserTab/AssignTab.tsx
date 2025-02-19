import React, { useState } from 'react';
import InputTextField from '../../../components/common/InputTextField';
import AssetModules from '../../../shared/AssetModules.js';
import Chips from '../../common/Chips';
import { CustomSelect } from '../../common/Select';
import Button from '@/components/common/Button';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const roleList = [
  { label: 'Project Manger', value: 'project_manager' },
  { label: 'Surveyor', value: 'surveyor' },
  { label: 'Supervisor', value: 'supervisor' },
];
const AssignTab = () => {
  useDocumentTitle('Manage Project: Assign User');
  const [user, setUser] = useState<string | null>('');
  const [assignUser, setAssignUser] = useState<string[]>([]);
  const [assignedRole, setAssignedRole] = useState<string>('');
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 lg:fmtm-gap-10">
      <div>
        <div className="fmtm-flex fmtm-gap-2">
          <div className="fmtm-flex-grow">
            <InputTextField
              id="name"
              name="name"
              label="Assign User"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              fieldType="text"
            />
          </div>
          <AssetModules.AddIcon
            className="fmtm-bg-red-600 fmtm-text-white fmtm-rounded-full hover:fmtm-bg-red-700 hover:fmtm-cursor-pointer fmtm-mt-9"
            onClick={() => {
              setAssignUser([...assignUser, user]);
              setUser('');
            }}
          />
        </div>
        {assignUser.length > 0 && (
          <div>
            <Chips
              data={assignUser}
              clearChip={(i) => {
                setAssignUser((prevAssignUser) => assignUser.filter((_, index) => index !== i));
              }}
            />
          </div>
        )}
      </div>
      <CustomSelect
        title="Assign as"
        placeholder="Choose"
        data={roleList}
        dataKey="value"
        value={assignedRole}
        valueKey="value"
        label="label"
        onValueChange={(value) => setAssignedRole(value)}
        className="fmtm-bg-white"
      />
      <div className="fmtm-flex fmtm-justify-center">
        <Button variant="primary-red">ASSIGN</Button>
      </div>
    </div>
  );
};

export default AssignTab;
