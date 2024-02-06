import React, { useState } from 'react';
import AssignTab from './AssignTab';
import InviteTab from './InviteTab';
import Table, { TableHeader } from '../../common/CustomTable';
import AssetModules from '../../../shared/AssetModules.js';
import KebabMenu from '../../common/KebabMenu';

const tabList: ['Assign', 'Invite'] = ['Assign', 'Invite'];
const data = [
  {
    id: 1,
    username: 'Adarsha Kumar Sharma',
    role: 'Municipal Admin',
    user_status: 'Active',
    last_contribution: '1/5/2024',
  },
  {
    id: 2,
    username: 'Adarsha Kumar Sharma',
    role: 'Municipal Admin',
    user_status: 'Active',
    last_contribution: '1/5/2024',
  },
  {
    id: 3,
    username: 'Adarsha Kumar Sharma',
    role: 'Municipal Admin',
    user_status: 'Active',
    last_contribution: '1/5/2024',
  },
  {
    id: 4,
    username: 'Adarsha Kumar Sharma',
    role: 'Municipal Admin',
    user_status: 'Active',
    last_contribution: '1/5/2024',
  },
  {
    id: 5,
    username: 'Adarsha Kumar Sharma',
    role: 'Municipal Admin',
    user_status: 'Active',
    last_contribution: '1/5/2024',
  },
];

const UserTab = () => {
  const [tabView, setTabView] = useState<'Assign' | 'Invite'>('Assign');
  const [openedModalId, setOpenedModalId] = useState('');

  const handleEdit = () => {};
  const handleDelete = () => {};
  const handleResendInvitation = () => {};

  return (
    <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 lg:fmtm-gap-10 fmtm-w-full">
      <div className="fmtm-max-w-[18rem] lg:fmtm-w-[23%] lg:fmtm-min-w-[18rem]">
        <div className="fmtm-flex fmtm-gap-3 fmtm-mb-5">
          {tabList.map((tab) => (
            <div
              key={tab}
              className={`fmtm-w-fit fmtm-text-[#9B9999] fmtm-px-2 fmtm-border-b-[1px] hover:fmtm-border-primaryRed fmtm-duration-300 fmtm-cursor-pointer ${
                tabView === tab ? 'fmtm-border-primaryRed' : 'fmtm-border-transparent'
              }`}
              onClick={() => setTabView(tab)}
            >
              {tab}
            </div>
          ))}
        </div>
        <div>{tabView === 'Assign' ? <AssignTab /> : <InviteTab />}</div>
      </div>
      <Table
        flag="primarytable"
        style={{ 'max-height': '60vh', width: '100%' }}
        data={data}
        onRowClick={() => {}}
        isLoading={false}
      >
        <TableHeader
          dataField="SN"
          headerClassName="snHeader"
          rowClassName="snRow"
          dataFormat={(row, _, index) => <span>{index + 1}</span>}
        />

        <TableHeader
          dataField="Username"
          headerClassName="codeHeader"
          rowClassName="codeRow"
          dataFormat={(row) => (
            <div className="fmtm-w-[18rem] fmtm-overflow-hidden fmtm-truncate" title={row?.username}>
              <span className="fmtm-text-[15px]">{row?.username}</span>
            </div>
          )}
        />
        <TableHeader
          dataField="Role"
          headerClassName="codeHeader"
          rowClassName="codeRow"
          dataFormat={(row) => (
            <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate" title={row?.role}>
              <span className="fmtm-text-[15px]">{row?.role}</span>
            </div>
          )}
        />
        <TableHeader
          dataField="User Status"
          headerClassName="codeHeader"
          rowClassName="codeRow"
          dataFormat={(row) => (
            <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate" title={row?.user_status}>
              <span className="fmtm-text-[15px]">{row?.user_status}</span>
            </div>
          )}
        />
        <TableHeader
          dataField="Last Contribution"
          headerClassName="codeHeader"
          rowClassName="codeRow"
          dataFormat={(row) => (
            <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate" title={row?.last_contribution}>
              <span className="fmtm-text-[15px]">{row?.last_contribution}</span>
            </div>
          )}
        />
        <TableHeader
          dataField=""
          headerClassName="codeHeader"
          rowClassName="codeRow"
          dataFormat={(row) => (
            <div className="fmtm-truncate fmtm-w-[1.5rem]" title={row?.last_contribution}>
              <div className="fmtm-absolute fmtm-top-[20%] fmtm-left-[15%]">
                <KebabMenu
                  stopPropagation
                  options={[
                    {
                      id: 1,
                      icon: <AssetModules.EditOutlinedIcon className="fmtm-text-[#757575]" />,
                      label: 'Edit',
                      onClick: handleEdit,
                    },
                    {
                      id: 2,
                      icon: <AssetModules.AutorenewIcon />,
                      label: 'Resend Invitation',
                      onClick: handleResendInvitation,
                    },
                    { id: 3, icon: <AssetModules.DeleteOutlinedIcon />, label: 'Remove', onClick: handleDelete },
                  ]}
                  pid={row.id}
                  data={row}
                  openedModalId={openedModalId}
                  onDropdownOpen={() => {
                    setOpenedModalId(row.id);
                  }}
                />
              </div>
            </div>
          )}
        />
      </Table>
    </div>
  );
};

export default UserTab;
