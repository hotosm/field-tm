import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import { Modal } from '@/components/common/Modal';
import { useLocation } from 'react-router-dom';
import { LoginActions } from '@/store/slices/LoginSlice';
import OSMImg from '@/assets/images/osm-logo.png';
import { useAppDispatch } from '@/types/reduxTypes';
import { useGetOsmLoginUrlQuery } from '@/api/auth';

type loginOptionsType = {
  id: string;
  name: string;
  icon?: React.ReactNode;
  image?: string;
};

const loginOptions: loginOptionsType[] = [
  {
    id: 'osm_account',
    name: 'Personal OSM Account',
    image: OSMImg,
  },
];

const LoginPopup = () => {
  const dispatch = useAppDispatch();
  const location = useLocation();
  const from = location.state?.from || '/';

  const loginModalOpen = CoreModules.useAppSelector((state) => state.login.loginModalOpen);

  const {
    data: osmLoginUrl,
    isSuccess,
    refetch: fetchOsmLoginUrl,
  } = useGetOsmLoginUrlQuery({
    options: {
      queryKey: ['osm-login-url'],
      enabled: false,
    },
  });

  const handleSignIn = async (selectedOption: string) => {
    if (selectedOption === 'osm_account') {
      sessionStorage.setItem('requestedPath', from);
      fetchOsmLoginUrl();
    }
  };

  useEffect(() => {
    const login_url = osmLoginUrl?.login_url;
    if (login_url && isSuccess) {
      window.location.href = login_url;
    }
  }, [osmLoginUrl, isSuccess]);

  const LoginDescription = () => {
    return (
      <div className="fmtm-flex fmtm-items-start fmtm-flex-col">
        <div className="fmtm-text-2xl fmtm-font-bold fmtm-mb-4">Sign In</div>
        <div className="fmtm-w-full fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-justify-items-center">
          {loginOptions?.map((option) => (
            <div
              key={option.id}
              onClick={() => handleSignIn(option.id)}
              className="fmtm-bg-[#F5F5F5] fmtm-border-gray-300 fmtm-text-gray-700 fmtm-w-full fmtm-py-3 fmtm-px-4 fmtm-rounded-md fmtm-duration-300 hover:fmtm-border-primaryRed hover:fmtm-text-primaryRed fmtm-border-[1px] fmtm-cursor-pointer fmtm-text-sm fmtm-flex fmtm-items-center fmtm-gap-3 fmtm-group"
            >
              <div className="fmtm-w-10 fmtm-max-w-10 fmtm-min-w-10">
                {option?.image ? <img src={option?.image} className="fmtm-w-full" /> : option?.icon}
              </div>
              <div className="fmtm-text-lg">{option.name}</div>
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
