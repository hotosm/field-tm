import React, { useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import { Modal } from '@/components/common/Modal';
import { useDispatch } from 'react-redux';
import { LoginActions } from '@/store/slices/LoginSlice';
import Button from './common/Button';
import { createLoginWindow } from '@/utilfunctions/login';
import { TemporaryLoginService } from '@/api/Login';
import AssetModules from '@/shared/AssetModules';
import OSMImg from '@/assets/images/osm-logo.png';

type loginOptionsType = {
  id: string;
  name: string;
  icon?: React.ReactNode;
  image?: string;
  description: string;
};

const loginOptions: loginOptionsType[] = [
  {
    id: 'osm_account',
    name: 'Personal OSM Account',
    image: OSMImg,
    description: 'If you want to Log in using your individual OSM account.',
  },
  {
    id: 'temp_account',
    name: 'Temporary Account',
    icon: <AssetModules.PersonIcon color="" sx={{ fontSize: '40px' }} className="fmtm-w-10 fmtm-h-10" />,
    description: "If you're not an OSM user or prefer not to create an OSM account.",
  },
];

const LoginPopup = () => {
  const dispatch = useDispatch();

  const [activeLogin, setActiveLogin] = useState('');
  const loginModalOpen = CoreModules.useAppSelector((state) => state.login.loginModalOpen);

  const updateStatus = (currentOption: string) => {
    if (currentOption === activeLogin) {
      setActiveLogin('');
    } else {
      setActiveLogin(currentOption);
    }
  };

  const handleSignIn = () => {
    if (activeLogin === 'osm_account') {
      createLoginWindow('/');
    } else {
      dispatch(TemporaryLoginService(`${import.meta.env.VITE_API_URL}/auth/login/`));
    }
  };

  const LoginDescription = () => {
    return (
      <div className="fmtm-flex fmtm-items-start fmtm-flex-col">
        <h2 className="fmtm-text-2xl fmtm-font-bold fmtm-mb-1">Sign In</h2>
        <p className="fmtm-text-base fmtm-mb-5 fmtm-text-gray-700">Sign In with any of the accounts</p>
        <div className="fmtm-w-full fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-justify-items-center">
          {loginOptions?.map((option) => (
            <div
              key={option.id}
              onClick={() => updateStatus(option.id)}
              className={`${
                activeLogin === option.id
                  ? 'fmtm-bg-red-50 fmtm-text-primaryRed fmtm-border-primaryRed'
                  : 'fmtm-bg-[#F5F5F5] fmtm-border-gray-300 fmtm-text-gray-700'
              } fmtm-w-full fmtm-py-3 fmtm-px-4 fmtm-rounded-md fmtm-duration-300 hover:fmtm-border-primaryRed hover:fmtm-text-primaryRed fmtm-border-[1px] fmtm-cursor-pointer fmtm-text-sm fmtm-flex fmtm-items-start fmtm-gap-3 fmtm-group`}
            >
              <div className="fmtm-w-10 fmtm-max-w-10 fmtm-min-w-10">
                {option?.image ? <img src={option?.image} className="fmtm-w-full" /> : option?.icon}
              </div>
              <div className="fmtm-flex fmtm-flex-col">
                <p className="fmtm-text-lg">{option.name}</p>
                <p className="">{option.description}</p>
              </div>
            </div>
          ))}
        </div>
        {activeLogin && (
          <div className="fmtm-w-full fmtm-flex fmtm-justify-center fmtm-mt-6">
            <Button
              btnText="Sign In"
              btnType="primary"
              onClick={handleSignIn}
              className="!fmtm-py-1 !fmtm-px-6 !fmtm-rounded-md"
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <Modal
        open={loginModalOpen}
        description={<LoginDescription />}
        onOpenChange={(openStatus) => {
          dispatch(LoginActions.setLoginModalOpen(openStatus));
        }}
        className="!fmtm-max-w-[35rem]"
      />
    </div>
  );
};

export default LoginPopup;
