import React from 'react';
import CoreModules from '@/shared/CoreModules';
import { Modal } from '@/components/common/Modal';
import { useDispatch } from 'react-redux';
import { useLocation } from 'react-router-dom';
import { LoginActions } from '@/store/slices/LoginSlice';
import { osmLoginRedirect } from '@/utilfunctions/login';
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
    description: 'Edits made in FMTM will be credited to your OSM account.',
  },
];

const LoginPopup = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  const from = location.state?.from || '/';

  const loginModalOpen = CoreModules.useAppSelector((state) => state.login.loginModalOpen);

  const handleSignIn = async (selectedOption: string) => {
    if (selectedOption === 'osm_account') {
      localStorage.setItem('requestedPath', from);
      osmLoginRedirect();
    }
  };

  const LoginDescription = () => {
    return (
      <div className="fmtm-flex fmtm-items-start fmtm-flex-col">
        <div className="fmtm-text-2xl fmtm-font-bold fmtm-mb-4">Sign In</div>
        <div className="fmtm-w-full fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-justify-items-center">
          {loginOptions?.map((option) => (
            <div
              key={option.id}
              onClick={() => handleSignIn(option.id)}
              className="fmtm-bg-[#F5F5F5] fmtm-border-gray-300 fmtm-text-gray-700 fmtm-w-full fmtm-py-3 fmtm-px-4 fmtm-rounded-md fmtm-duration-300 hover:fmtm-border-primaryRed hover:fmtm-text-primaryRed fmtm-border-[1px] fmtm-cursor-pointer fmtm-text-sm fmtm-flex fmtm-items-start fmtm-gap-3 fmtm-group"
            >
              <div className="fmtm-w-10 fmtm-max-w-10 fmtm-min-w-10">
                {option?.image ? <img src={option?.image} className="fmtm-w-full" /> : option?.icon}
              </div>
              <div className="fmtm-flex fmtm-flex-col">
                <div className="fmtm-text-lg">{option.name}</div>
                <div className="">{option.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <>
      <Modal
        open={loginModalOpen}
        description={<LoginDescription />}
        onOpenChange={(openStatus) => {
          dispatch(LoginActions.setLoginModalOpen(openStatus));
        }}
        className="!fmtm-max-w-[35rem]"
      />
    </>
  );
};

export default LoginPopup;
