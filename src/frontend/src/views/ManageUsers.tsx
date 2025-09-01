import React, { useState } from 'react';
import DataTable from '@/components/common/DataTable';
import { UpdateUserRole } from '@/api/User';
import { useAppDispatch } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/common/Dropdown';
import { user_roles } from '@/types/enums';
import { CommonActions } from '@/store/slices/CommonSlice';
import Searchbar from '@/components/common/SearchBar';
import useDebouncedInput from '@/hooks/useDebouncedInput';
import { useIsAdmin } from '@/hooks/usePermissions';
import Forbidden from '@/views/Forbidden';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useGetUsersQuery } from '@/api/user';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type roleType = 'READ_ONLY' | 'ADMIN' | 'MAPPER';
const roleLabel = {
  READ_ONLY: 'Read Only',
  MAPPER: 'Mapper',
  ADMIN: 'Admin',
};

const ManageUsers = () => {
  useDocumentTitle('Manage Users');
  const dispatch = useAppDispatch();

  const isAdmin = useIsAdmin();
  if (!isAdmin) return <Forbidden />;

  const updateRole = (userSub: string, currentRole: roleType, newRole: roleType) => {
    if (currentRole === newRole) {
      dispatch(CommonActions.SetSnackBar({ message: 'Role up-to-date', variant: 'info' }));
      return;
    }
    dispatch(UpdateUserRole(`${VITE_API_URL}/users/${userSub}`, { role: newRole }));
  };

  const userDatacolumns = [
    {
      header: 'Users',
      accessorKey: 'username',
      cell: ({ row }: any) => {
        const currRow = row?.original;
        return (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            {!currRow?.profile_img ? (
              <div className="fmtm-w-[1.875rem] fmtm-h-[1.875rem] fmtm-rounded-full fmtm-bg-[#68707F] fmtm-flex fmtm-items-center fmtm-justify-center fmtm-cursor-default">
                <p className="fmtm-text-white">{currRow?.username[0]?.toUpperCase()}</p>
              </div>
            ) : (
              <img
                src={currRow?.profile_img}
                className="fmtm-w-[1.875rem] fmtm-h-[1.875rem] fmtm-rounded-full"
                alt="profile image"
              />
            )}
            <a
              target="_"
              href={
                currRow?.sub?.split('|')[0] === 'osm'
                  ? `https://www.openstreetmap.org/user/${currRow?.username}`
                  : `mailto:${currRow?.email_address}`
              }
              className="fmtm-text-red-medium hover:fmtm-text-red-dark fmtm-underline"
            >
              {currRow?.username}
            </a>
          </div>
        );
      },
    },
    {
      header: 'Sign-in Method',
      accessorKey: 'sub',
      cell: ({ getValue }) => {
        return <p className="fmtm-capitalize">{getValue()?.split('|')[0]}</p>;
      },
    },
    {
      header: 'Role',
      accessorKey: 'role',
      cell: ({ row }: any) => {
        return <>{roleLabel[row?.original?.role]}</>;
      },
    },
    {
      header: 'Last Active',
      accessorKey: 'last_login_at',
      cell: ({ row }: any) => {
        const lastActive = row?.original?.last_login_at ? row?.original?.last_login_at?.split('T')[0] : 'N/A';
        return <>{lastActive}</>;
      },
    },
    {
      header: ' ',
      cell: ({ row }: any) => {
        const userSub = row?.original?.sub;
        const currentRole = row?.original?.role;
        return (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger className="fmtm-outline-none">
                <AssetModules.ManageAccountsOutlinedIcon className="fmtm-cursor-pointer hover:fmtm-text-primaryRed" />
              </DropdownMenuTrigger>
              <DropdownMenuContent className="fmtm-z-[50] fmtm-bg-white" align="end">
                {Object.keys(user_roles)?.map((role) => (
                  <DropdownMenuItem
                    key={role}
                    className="hover:fmtm-bg-red-50 fmtm-duration-200 fmtm-outline-none fmtm-py-1 fmtm-px-4 fmtm-cursor-pointer fmtm-rounded"
                    onSelect={() => {
                      updateRole(userSub, currentRole as roleType, role as roleType);
                    }}
                  >
                    {roleLabel[role]}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        );
      },
    },
  ];

  const [filter, setFilter] = useState({ search: '', page: 1, results_per_page: 1 });
  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 500,
    init: filter.search,
    onChange: (debouncedEvent) => setFilter((prev) => ({ ...prev, search: debouncedEvent.target.value })),
  });

  const { data: userList, isLoading: isUserListLoading } = useGetUsersQuery({
    params: filter,
    options: { queryKey: ['get-users', filter] },
  });

  return (
    <div className="fmtm-h-full fmtm-flex fmtm-flex-col">
      <div className="fmtm-flex fmtm-items-center fmtm-justify-between">
        <h4 className="fmtm-font-semibold fmtm-text-[#2C3038]">Manage Users</h4>
        <Searchbar
          value={searchTextData}
          onChange={handleChangeData}
          wrapperStyle="!fmtm-w-[13rem]"
          className="!fmtm-py-0 !fmtm-rounded"
          placeholder="Search by username"
          isSmall
        />
      </div>
      <p className="fmtm-body-md-semibold fmtm-text-grey-500 fmtm-mb-4">
        Total number of users: {userList?.pagination?.total}
      </p>
      <DataTable
        data={userList || []}
        columns={userDatacolumns}
        isLoading={isUserListLoading}
        pagination={{ pageIndex: filter.page, pageSize: 13 }}
        setPaginationPage={(page) => setFilter((prev) => ({ ...prev, pageIndex: page + 1 }))}
        tableWrapperClassName="fmtm-flex-1"
      />
    </div>
  );
};

export default ManageUsers;
