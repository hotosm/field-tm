import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules.js';
import { InviteNewUser } from '@/api/User';
import Button from '@/components/common/Button';
import Chips from '@/components/common/Chips.js';
import Select2 from '@/components/common/Select2.js';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { inviteValidationSchema } from '@/components/ManageProject/User/validation/inviteValidation';
import RadioButton from '@/components/common/RadioButton';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import InviteTable from './InviteTable';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import isEmpty from '@/utilfunctions/isEmpty';
import { UserActions } from '@/store/slices/UserSlice';
import { inviteUserDefaultValue } from './constants/defaultValues';
import { inviteOptions, invitePropType } from './constants';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import ErrorMessage from '@/components/common/ErrorMessage';
import { Textarea } from '@/components/RadixComponents/TextArea';
import FieldLabel from '@/components/common/FieldLabel';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const InviteTab = ({ roleList }: invitePropType) => {
  useDocumentTitle('Manage Project: Invite User');
  const dispatch = useAppDispatch();
  const params = useParams();

  const projectId = +params.id!;
  const [user, setUser] = useState('');

  const inviteNewUserPending = useAppSelector((state) => state.user.inviteNewUserPending);
  const projectUserInvitesError = useAppSelector((state) => state.user.projectUserInvitesError);

  const onSubmit = () => {
    const values = getValues();
    dispatch(InviteNewUser(`${VITE_API_URL}/users/invite`, { ...values, projectId }));
  };

  const formMethods = useForm({
    defaultValues: inviteUserDefaultValue,
    resolver: zodResolver(inviteValidationSchema),
  });
  const { watch, control, setValue, formState, handleSubmit, getValues } = formMethods;
  const { errors } = formState;
  const values = watch();

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
              <p className="fmtm-text-red-medium" key={i + 1}>
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
          onSubmit={handleSubmit(onSubmit)}
          className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-bg-white fmtm-rounded-xl fmtm-p-6 md:fmtm-w-[17.5rem] md:fmtm-min-w-[17.5rem] md:fmtm-h-full md:fmtm-overflow-y-scroll md:scrollbar"
        >
          <>
            <Controller
              control={control}
              name={'inviteVia'}
              render={({ field }) => (
                <RadioButton
                  value={field.value}
                  options={inviteOptions}
                  onChangeData={field.onChange}
                  ref={field.ref}
                  className="!fmtm-text-base fmtm-text-gray-800"
                />
              )}
            />
            {errors?.inviteVia?.message && <ErrorMessage message={errors.inviteVia.message as string} />}
          </>
          <div className="fmtm-w-full">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-mb-2">
              <FieldLabel label="Invite User" astric />
              <Controller
                control={control}
                name="user"
                render={({ field }) => (
                  <Textarea
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
                    ref={field.ref}
                  />
                )}
              />
              <Button
                disabled={!user}
                variant="secondary-grey"
                onClick={() => {
                  if (!user) return;
                  if (values.inviteVia === 'osm') {
                    setValue('user', [...values.user, ...user.split(',')]);
                  } else {
                    setValue('user', [...values.user, ...user.split(' ')]);
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
                  setValue(
                    'user',
                    values.user.filter((_, index) => index !== i),
                  );
                }}
                className="fmtm-w-full fmtm-flex-wrap"
              />
            )}
            {errors?.user?.message && <ErrorMessage message={errors.user.message as string} />}
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
            <FieldLabel label="Assign as" astric />
            <Controller
              control={control}
              name="role"
              render={({ field }) => (
                <Select2
                  options={roleList || []}
                  value={field.value as string}
                  choose="id"
                  onChange={(value: any) => {
                    field.onChange(value);
                  }}
                  placeholder="Role"
                  ref={field.ref}
                />
              )}
            />
            {errors?.role?.message && <ErrorMessage message={errors.role.message as string} />}
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
