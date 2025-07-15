import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import Select2 from '@/components/common/Select2';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { GetUserNames } from '@/api/User';
import { UserActions } from '@/store/slices/UserSlice';
import { AddOrganizationAdminService } from '@/api/OrganisationService';
import isEmpty from '@/utilfunctions/isEmpty';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const AddOrganizationAdminModal = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const lastFetchedPrefix = useRef('');

  const [toggleModal, setToggleModal] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedAdmins, setSelectedAdmins] = useState([]);

  const organizationId = params.id;
  const userNames = useAppSelector((state) => state.user.userNames)?.map((user) => ({
    id: user.sub,
    label: user.username,
    value: user.sub,
  }));
  const addOrganizationAdminPending = useAppSelector((state) => state.organisation.addOrganizationAdminPending);

  const searchUser = (searchTxt) => {
    if (!organizationId) return;
    dispatch(
      GetUserNames(`${VITE_API_URL}/users/usernames`, {
        org_id: +organizationId,
        search: searchTxt,
        signin_type: 'osm',
      }),
    );
  };

  const assignOrganizationAdmins = async () => {
    if (!organizationId) return;
    await dispatch(
      AddOrganizationAdminService(`${VITE_API_URL}/organisation/new-admin`, selectedAdmins, +organizationId),
    );
    setToggleModal(false);
  };

  useEffect(() => {
    const trimmedText = searchText.trim();

    if (trimmedText.length >= 3) {
      const currentPrefix = trimmedText.slice(0, 3);

      if (currentPrefix !== lastFetchedPrefix.current) {
        lastFetchedPrefix.current = currentPrefix;
        searchUser(currentPrefix);
        lastFetchedPrefix.current = '';
      }
    } else {
      dispatch(UserActions.SetUserNames([]));
    }
  }, [searchText]);

  return (
    <Dialog open={toggleModal} onOpenChange={setToggleModal}>
      <DialogTrigger className="fmtm-w-fit">
        <Button variant="secondary-red">
          <AssetModules.AddIcon />
          Add Admin
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Assign Organization Admin</DialogTitle>
        <div>
          <Select2
            name="org_admins"
            options={userNames?.filter((user) => user.label?.includes(searchText)) || []}
            value={selectedAdmins}
            onChange={(value: any) => {
              setSelectedAdmins(value);
            }}
            placeholder="Search for FMTM users"
            className="naxatw-w-1/5 naxatw-min-w-[9rem]"
            multiple
            checkBox
            isLoading={false}
            handleApiSearch={(value) => {
              setSearchText(value);
            }}
          />
          <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
            <Button variant="link-grey" onClick={() => setToggleModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary-red"
              isLoading={addOrganizationAdminPending}
              disabled={isEmpty(selectedAdmins)}
              onClick={assignOrganizationAdmins}
            >
              Assign
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AddOrganizationAdminModal;
