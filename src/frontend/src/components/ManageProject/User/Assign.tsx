import React, { useState } from 'react';
import AssetModules from '@/shared/AssetModules.js';
import Button from '@/components/common/Button';
import Chips from '@/components/common/Chips';
import InputTextField from '@/components/common/InputTextField.js';
import Select2 from '@/components/common/Select2';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { project_roles } from '@/types/enums';

type propType = {
  roleList: {
    id: string;
    value: project_roles;
    label: string;
  }[];
};

const AssignTab = ({ roleList }: propType) => {
  useDocumentTitle('Manage Project: Assign User');
  const [user, setUser] = useState<string | null>('');
  const [assignUser, setAssignUser] = useState<string[]>([]);
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 lg:fmtm-gap-10 fmtm-bg-white fmtm-p-6">
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
      <div className="fmtm-flex fmtm-justify-center">
        <Button variant="primary-red">ASSIGN</Button>
      </div>
    </div>
  );
};

export default AssignTab;
