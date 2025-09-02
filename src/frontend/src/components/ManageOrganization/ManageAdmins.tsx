import React, { useState } from 'react';
import DataTable from '@/components/common/DataTable';
import { useAppDispatch } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import Button from '@/components/common/Button';
import { useParams } from 'react-router-dom';
import { OrganizationAdminsModel } from '@/models/organisation/organisationModel';
import { useGetOrganisationAdminsQuery, useRemoveOrganisationAdminMutation } from '@/api/organisation';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useQueryClient } from '@tanstack/react-query';

const ManageAdmins = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const queryClient = useQueryClient();

  const organizationId = params.id;
  const [toggleDeleteOrgModal, setToggleDeleteOrgModal] = useState(false);
  const [adminToRemove, setAdminToRemove] = useState<OrganizationAdminsModel | null>(null);

  const { data: organizationAdmins, isLoading: isOrganizationAdminsLoading } = useGetOrganisationAdminsQuery({
    params: { org_id: +organizationId! },
    options: { queryKey: ['get-org-admins', +organizationId!], enabled: !!organizationId },
  });

  const { mutate: removeOrganisationAdmin, isPending: isRemoveOrganisationAdminPending } =
    useRemoveOrganisationAdminMutation({
      options: {
        onSuccess: () => {
          dispatch(
            CommonActions.SetSnackBar({ message: 'Organisation admin removed successfully', variant: 'success' }),
          );
          queryClient.invalidateQueries({ queryKey: ['get-org-admins', +organizationId!] });
        },
        onError: ({ response }) => {
          dispatch(
            CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to remove organisation admin' }),
          );
        },
      },
    });

  const userDatacolumns = [
    {
      header: 'S.N',
      cell: ({ cell }: { cell: any }) => cell.row.index + 1,
    },
    {
      header: 'Users',
      accessorKey: 'username',
      cell: ({ row }: any) => {
        return (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            {!row?.original?.profile_img ? (
              <div className="fmtm-w-[1.875rem] fmtm-h-[1.875rem] fmtm-rounded-full fmtm-bg-[#68707F] fmtm-flex fmtm-items-center fmtm-justify-center fmtm-cursor-default">
                <p className="fmtm-text-white">{row?.original?.username[0]?.toUpperCase()}</p>
              </div>
            ) : (
              <img
                src={row?.original?.profile_img}
                className="fmtm-w-[1.875rem] fmtm-h-[1.875rem] fmtm-rounded-full"
                alt="profile image"
              />
            )}
            <p>{row?.original?.username}</p>
          </div>
        );
      },
    },
    {
      header: ' ',
      cell: ({ row }: any) => {
        const user = row?.original;
        return (
          <>
            <Dialog open={toggleDeleteOrgModal} onOpenChange={setToggleDeleteOrgModal}>
              <DialogTrigger>
                <AssetModules.DeleteOutlinedIcon
                  className="fmtm-cursor-pointer hover:fmtm-text-primaryRed"
                  onClick={() => setAdminToRemove(user)}
                />
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Remove Organization Admin?</DialogTitle>
                </DialogHeader>
                <div>
                  <p className="fmtm-body-lg fmtm-mb-1">
                    Are you sure you want to remove <b>{adminToRemove?.username}</b> as organization admin?
                  </p>
                  <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
                    <Button variant="link-grey" onClick={() => setToggleDeleteOrgModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="primary-red"
                      isLoading={isRemoveOrganisationAdminPending}
                      onClick={() => {
                        adminToRemove && removeOrgAdmin(adminToRemove?.user_sub);
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </>
        );
      },
    },
  ];

  const removeOrgAdmin = async (user_sub: string) => {
    if (!organizationId) return;
    removeOrganisationAdmin({ user_sub, params: { org_id: +organizationId } });
    setToggleDeleteOrgModal(false);
  };

  return (
    <div className="fmtm-h-full fmtm-flex fmtm-flex-col fmtm-py-6 fmtm-max-w-[37.5rem] fmtm-mx-auto">
      <DataTable
        data={organizationAdmins || []}
        columns={userDatacolumns}
        isLoading={isOrganizationAdminsLoading}
        tableWrapperClassName="fmtm-flex-1"
      />
    </div>
  );
};

export default ManageAdmins;
