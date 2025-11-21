import React, { useRef } from 'react';
import DataTable from '@/components/common/DataTable';
import { useParams } from 'react-router-dom';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/common/Dropdown';
import AssetModules from '@/shared/AssetModules';
import { useProjectUserInvitesQuery } from '@/api/user';

function getStatusStyle(status: 'Active' | 'Pending' | 'Expired' | '') {
  switch (status) {
    case 'Active':
      return 'fmtm-bg-[#40AC8C] fmtm-text-white';
    case 'Pending':
      return 'fmtm-bg-[#FCECA4] fmtm-text-black';
    case 'Expired':
      return 'fmtm-bg-[#FB7356] fmtm-text-white';
    default:
      return '';
  }
}

const InviteTable = () => {
  const params = useParams();
  const copyTextRef = useRef<HTMLElement>(null);
  const { protocol, hostname, port } = window.location;

  const projectId = +params.id!;

  const { data: projectUserInvites, isLoading: projectUserInvitesLoading } = useProjectUserInvitesQuery({
    params: { project_id: projectId },
    options: {
      queryKey: ['project-user-invites', projectId],
    },
  });

  const projectUserInvitesDataColumns = [
    {
      header: 'S.N',
      cell: ({ cell }: { cell: any }) => cell.row.index + 1,
    },
    {
      header: 'User',
      cell: ({ row }: any) => {
        return <>{row.original?.osm_username || row.original?.email}</>;
      },
    },
    {
      header: 'Role',
      accessorKey: 'role',
    },
    {
      header: 'User Status',
      cell: ({ row }: any) => {
        const { expires_at, used_at } = row?.original;
        const expiryDate = new Date(expires_at);
        const now = new Date();

        const userStatus = () => {
          if (used_at) {
            return 'Active';
          } else if (expiryDate.getTime() - now.getTime() > 0 && !used_at) {
            return 'Pending';
          } else if (expiryDate.getTime() - now.getTime() < 0 && !used_at) {
            return 'Expired';
          }
          return '';
        };

        return (
          <span
            className={`${getStatusStyle(userStatus())} fmtm-border-[1px] fmtm-border-gray-200 fmtm-py-1 fmtm-px-2 fmtm-rounded-2xl`}
          >
            {userStatus()}
          </span>
        );
      },
    },
    {
      header: ' ',
      cell: ({ row }: any) => {
        const data = row?.original;
        const baseUrl = row?.original?.email
          ? `${protocol}//mapper.${hostname}${port ? `:${port}` : ''}`
          : `${protocol}//${hostname}${port ? `:${port}` : ''}`;
        return (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger className="fmtm-outline-none">
                <AssetModules.MoreVertIcon className="fmtm-cursor-pointer hover:fmtm-text-primaryRed" />
              </DropdownMenuTrigger>
              <DropdownMenuContent className="fmtm-z-[50] fmtm-bg-white" align="end">
                <DropdownMenuItem
                  className="hover:fmtm-bg-red-50 fmtm-duration-200 fmtm-outline-none fmtm-p-1 fmtm-cursor-pointer fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-rounded fmtm-body-md"
                  onSelect={() => {
                    navigator.clipboard.writeText(`${baseUrl}/invite?token=${data.token}`);
                    if (copyTextRef.current) copyTextRef.current.textContent = 'Copied!';
                  }}
                >
                  <AssetModules.ContentCopyIcon className="!fmtm-text-sm hover:fmtm-text-primaryRed" />
                  <span ref={copyTextRef}>Copy invite link</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        );
      },
    },
  ];

  return (
    <DataTable
      data={projectUserInvites || []}
      columns={projectUserInvitesDataColumns}
      isLoading={projectUserInvitesLoading}
      tableWrapperClassName="fmtm-flex-1 fmtm-h-full"
    />
  );
};

export default InviteTable;
