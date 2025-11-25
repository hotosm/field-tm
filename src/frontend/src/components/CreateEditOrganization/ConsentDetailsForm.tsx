import React, { useEffect } from 'react';
import { CustomCheckbox } from '@/components/common/Checkbox';
import RadioButton from '@/components/common/RadioButton';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import InstructionsSidebar from '@/components/CreateEditOrganization/InstructionsSidebar';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { consentQuestions } from './constants';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { consentValidationSchema } from './validation/ConsentDetailsValidation';
import { consentDefaultValues } from './constants/consentDefaultValues';
import ErrorMessage from '@/components/common/ErrorMessage';

const ConsentDetailsForm = () => {
  useDocumentTitle('Consent Details Form');
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const consentDetailsFormData = useAppSelector((state) => state.organisation.consentDetailsFormData);

  const formMethods = useForm({
    defaultValues: consentDefaultValues,
    resolver: zodResolver(consentValidationSchema),
  });
  const { watch, control, setValue, formState, handleSubmit, reset, getValues } = formMethods;
  const { errors } = formState;
  const values = watch();

  useEffect(() => {
    reset(consentDetailsFormData);
  }, [consentDetailsFormData]);

  const onSubmit = () => {
    const values = getValues();
    dispatch(OrganisationAction.SetConsentApproval(true));
    dispatch(OrganisationAction.SetConsentDetailsFormData(values));
  };

  return (
    <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 lg:fmtm-gap-10 fmtm-h-full">
      <InstructionsSidebar />
      <form
        className="fmtm-h-full fmtm-flex fmtm-flex-col lg:fmtm-w-[70%] xl:fmtm-w-[55rem]"
        onSubmit={handleSubmit(onSubmit)}
      >
        <div className="fmtm-bg-white fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-h-[calc(100%-39px)] fmtm-overflow-y-scroll scrollbar">
          <h5 className="fmtm-text-[#484848] fmtm-text-2xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7">Consent Details</h5>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
            {consentQuestions.map((question) => (
              <div key={question.id}>
                <div className="fmtm-mb-3 fmtm-flex fmtm-flex-col">
                  <h6 className="fmtm-text-lg">
                    {question.question} {question.required && <span className="fmtm-text-red-500">*</span>}
                  </h6>
                  {question.description && <p className="fmtm-text-[#7A7676]">{question.description}</p>}
                </div>
                {question.type === 'radio' ? (
                  <>
                    <Controller
                      control={control}
                      name={question.id}
                      render={({ field }) => (
                        <RadioButton
                          value={field.value as string}
                          options={question.options}
                          onChangeData={field.onChange}
                          ref={field.ref}
                          className="!fmtm-text-base fmtm-text-gray-800"
                        />
                      )}
                    />
                    {errors?.[question.id]?.message && (
                      <ErrorMessage message={errors[question.id]?.message as string} />
                    )}
                  </>
                ) : (
                  <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
                    {question.options.map((option) => (
                      <CustomCheckbox
                        key={option.id}
                        label={option.label}
                        checked={values[question.id].includes(option.id)}
                        onCheckedChange={(checked) => {
                          return checked
                            ? setValue(question.id, [...values[question.id], option.id])
                            : setValue(
                                question.id,
                                values[question.id].filter((value) => value !== option.id),
                              );
                        }}
                      />
                    ))}
                    {errors?.[question.id]?.message && (
                      <ErrorMessage message={errors[question.id]?.message as string} />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-py-2 fmtm-bg-white fmtm-shadow-2xl">
          <Button variant="secondary-red" onClick={() => navigate('/organization')}>
            Cancel
          </Button>
          <Button variant="primary-red" type="submit">
            Next
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ConsentDetailsForm;
