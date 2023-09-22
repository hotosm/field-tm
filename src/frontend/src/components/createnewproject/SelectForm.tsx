import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { CommonActions } from '../../store/slices/CommonSlice';
import Button from '../../components/common/Button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/common/Select';
import { useNavigate } from 'react-router-dom';

const selectFormWaysList = ['Use Existing Form', 'Upload a Custom Form'];

const SelectForm = ({ flag }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const selectFormWays = selectFormWaysList.map((item) => ({ label: item, value: item }));

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };
  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Select Form</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>Fill in your project basic information such as name, description, hashtag, etc. </span>
          <span>To complete the first step, you will need the account credentials of ODK central server.</span>{' '}
          <span>Here are the instructions for setting up a Central ODK Server on Digital Ocean.</span>
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-8">
              <div>
                <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold ">Select form category</p>
                <div className="fmtm-flex fmtm-items-end ">
                  <div className="fmtm-w-[14rem]">
                    <Select
                    // value={values.value}
                    // onValueChange={(value) => handleCustomChange('organisation_id', value)}
                    >
                      <SelectTrigger className="">
                        <SelectValue placeholder="Select form category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {selectFormWays?.map((formWay) => (
                            <SelectItem key={formWay.value} value={formWay.value}>
                              {formWay.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <div>
                <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold ">Select form</p>
                <div className="fmtm-flex fmtm-items-end ">
                  <div className="fmtm-w-[14rem]">
                    <Select
                    // value={values.value}
                    // onValueChange={(value) => handleCustomChange('organisation_id', value)}
                    >
                      <SelectTrigger className="">
                        <SelectValue placeholder="Select form" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {selectFormWays?.map((formWay) => (
                            <SelectItem key={formWay.value} value={formWay.value}>
                              {formWay.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(4, '/define-tasks')}
                className="fmtm-font-bold"
              />
              <Button
                btnText="SUBMIT"
                btnType="primary"
                type="button"
                onClick={() => console.log('submit')}
                className="fmtm-font-bold"
              />
            </div>
          </div>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full"></div>
        </div>
      </div>
    </div>
  );
};

export default SelectForm;
