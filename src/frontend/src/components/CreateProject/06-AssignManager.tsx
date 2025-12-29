import React from 'react';
import { useFormContext } from 'react-hook-form';
import { createProjectValidationSchema } from './validation';
import { z } from 'zod/v4';
import FieldLabel from '@/components/common/FieldLabel';
import ErrorMessage from '@/components/common/ErrorMessage';
import { Input } from '@/components/RadixComponents/Input';

const AssignManager = () => {
  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, formState, setValue } = form;
  const { errors } = formState;
  const values = watch();

  const tabs = [
    { isNew: true, label: `New User (Don't have ${values.field_mapping_app} )` },
    { isNew: false, label: `Already have ${values.field_mapping_app} account` },
  ];

  return (
    <div>
      <div className="fmtm-grid fmtm-grid-cols-2 fmtm-w-full">
        {tabs.map((tab, i) => (
          <div
            key={i}
            role="button"
            onClick={() => setValue('has_external_mappingapp_account', !values.has_external_mappingapp_account)}
            className={`fmtm-button fmtm-mx-auto fmtm-w-full fmtm-text-center fmtm-border-b-2 fmtm-cursor-pointer fmtm-py-1 hover:fmtm-bg-gray-50 fmtm-duration-150 ${!values.has_external_mappingapp_account === tab.isNew ? 'fmtm-border-red-medium' : 'fmtm-border-gray-100'}`}
          >
            {tab.label}
          </div>
        ))}
      </div>
      <div className="fmtm-py-5">
        {!values.has_external_mappingapp_account ? (
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label={`Enter ${values.field_mapping_app} Email/Username`} astric />
              <Input {...register('external_project_username')} />
              {errors?.external_project_username?.message && (
                <ErrorMessage message={errors.external_project_username.message as string} />
              )}
            </div>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Enter New Password" astric />
              <Input {...register('external_project_password')} />
              {errors?.external_project_password?.message && (
                <ErrorMessage message={errors.external_project_password.message as string} />
              )}
            </div>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Enter New Password (Retype to Confirm)" astric />
              <Input {...register('external_project_password_confirm')} />
              {errors?.external_project_password_confirm?.message && (
                <ErrorMessage message={errors.external_project_password_confirm.message as string} />
              )}
            </div>
          </div>
        ) : (
          <div>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label={`Enter ${values.field_mapping_app} Email/Username`} astric />
              <Input {...register('external_project_username')} />
              {errors?.external_project_username?.message && (
                <ErrorMessage message={errors.external_project_username.message as string} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssignManager;
