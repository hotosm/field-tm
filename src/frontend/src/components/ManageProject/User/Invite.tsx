import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules.js';
import useForm from '@/hooks/useForm';
import { InviteNewUser } from '@/api/User';
import Button from '@/components/common/Button';
import Chips from '@/components/common/Chips.js';
import Select2 from '@/components/common/Select2.js';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { project_roles } from '@/types/enums';
import InviteValidation from '@/components/ManageProject/User/validation/InviteValidation';
import RadioButton from '@/components/common/RadioButton';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import InviteTable from './InviteTable';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import isEmpty from '@/utilfunctions/isEmpty';
import { UserActions } from '@/store/slices/UserSlice';
import TextArea from '@/components/common/TextArea';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type propType = {
  roleList: {
    id: string;
    value: project_roles;
    label: string;
  }[];
};

const inviteOptions = [
  {
    name: 'invite_options',
    value: 'osm',
    label: 'Invite via OSM',
  },
  {
    name: 'invite_options',
    value: 'gmail',
    label: 'Invite via Gmail',
  },
];

const initialFormState = {
  inviteVia: 'osm',
  user: [],
  role: null,
};

const InviteTab = ({ roleList }: propType) => {
  useDocumentTitle('Manage Project: Invite User');
  const dispatch = useAppDispatch();
  const params = useParams();

  const projectId = params.id;
  const [user, setUser] = useState('');

  const inviteNewUserPending = useAppSelector((state) => state.user.inviteNewUserPending);
  const projectUserInvitesError = useAppSelector((state) => state.user.projectUserInvitesError);

  const submission = () => {
    dispatch(InviteNewUser(`${VITE_API_URL}/users/invite`, { ...values, projectId }));
  };

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    initialFormState,
    submission,
    InviteValidation,
  );

  return (
    <>
      <Dialog
        open={!isEmpty(projectUserInvitesError)}
        onOpenChange={(state) => {
          if (!state) dispatch(UserActions.SetProjectUserInvitesError([]));
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>There were some problems while inviting users</DialogTitle>
          </DialogHeader>
          <div className="fmtm-border-[1px] fmtm-p-2 fmtm-border-red-medium fmtm-rounded-lg fmtm-bg-red-50">
            {projectUserInvitesError.map((inviteError, i) => (
              <p className="fmtm-text-red-medium">
                {i + 1}. {inviteError}
              </p>
            ))}
          </div>
          <Button
            variant="primary-grey"
            className="fmtm-ml-auto"
            onClick={() => dispatch(UserActions.SetProjectUserInvitesError([]))}
          >
            Dismiss
          </Button>
        </DialogContent>
      </Dialog>

      <div className="fmtm-flex fmtm-flex-col md:fmtm-flex-row fmtm-h-[calc(100%-24px)] fmtm-w-full fmtm-gap-5">
        <form
          onSubmit={handleSubmit}
          className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-bg-white fmtm-rounded-xl fmtm-p-6 md:fmtm-w-[17.5rem] md:fmtm-min-w-[17.5rem] md:fmtm-h-full md:fmtm-overflow-y-scroll md:scrollbar"
        >
          <RadioButton
            value={values?.inviteVia || ''}
            topic=""
            options={inviteOptions}
            direction="row"
            onChangeData={(value) => {
              handleCustomChange('inviteVia', value);
            }}
          />
          <div className="fmtm-w-full">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-mb-2">
              <TextArea
                id="name"
                name="name"
                label="Invite User"
                value={user}
                onChange={(e) => {
                  if (values.inviteVia === 'osm') {
                    setUser(e.target.value.replace(/[\r\n]+/g, ', '));
                  } else {
                    setUser(e.target.value.replace(/[\r\n]+/g, ' ').replace(/\t/g, ' '));
                  }
                }}
                placeholder={
                  values.inviteVia === 'osm'
                    ? 'Enter Username (To assign multiple users, separate osm usernames with commas)'
                    : 'Enter Gmail (To assign multiple users, separate gmail addresses with space)'
                }
                rows={5}
                required
              />
              <Button
                disabled={!user}
                variant="secondary-grey"
                onClick={() => {
                  if (!user) return;
                  if (values.inviteVia === 'osm') {
                    handleCustomChange('user', [...values.user, ...user.split(',')]);
                  } else {
                    handleCustomChange('user', [...values.user, ...user.split(' ')]);
                  }
                  setUser('');
                }}
                className="fmtm-ml-auto"
              >
                <AssetModules.AddIcon className="!fmtm-text-base" />
                Add
              </Button>
            </div>
            {values.user.length > 0 && (
              <Chips
                data={values.user}
                clearChip={(i) => {
                  handleCustomChange(
                    'user',
                    values.user.filter((_, index) => index !== i),
                  );
                }}
                className="fmtm-w-full fmtm-flex-wrap"
              />
            )}
            {errors?.user && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm">{errors.user}</p>}
          </div>
          <div>
            <p className={`fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent`}>
              Assign as <span className="fmtm-text-red-500 fmtm-text-[1.2rem] fmtm-font-normal">*</span>
            </p>
            <Select2
              options={roleList || []}
              value={values.role}
              onChange={(value: any) => {
                handleCustomChange('role', value);
              }}
              placeholder="Role"
              className="naxatw-w-1/5 naxatw-min-w-[9rem]"
            />
            {errors.role && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm">{errors.role}</p>}
          </div>
          <div className="fmtm-flex fmtm-justify-center">
            <Button type="submit" variant="primary-red" isLoading={inviteNewUserPending}>
              ASSIGN
            </Button>
          </div>
        </form>
        <div className="fmtm-flex-1 md:fmtm-w-[calc(100%-20rem)] fmtm-overflow-hidden">
          <InviteTable />
        </div>
      </div>
    </>
  );
};

export default InviteTab;
