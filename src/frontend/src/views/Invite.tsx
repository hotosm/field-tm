import React, { useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { AcceptInvite } from '@/api/User';
import { useAppDispatch } from '@/types/reduxTypes';
import { Loader2 } from 'lucide-react';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const Invite = () => {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      dispatch(AcceptInvite(`${VITE_API_URL}/users/invite/${token}`, navigate));
    } else {
      navigate('/explore');
    }
  }, [token]);

  return (
    <div className="fmtm-h-full fmtm-flex fmtm-flex-col fmtm-justify-center fmtm-items-center">
      <Loader2 className="fmtm-h-10 fmtm-w-10 fmtm-animate-spin fmtm-text-primaryRed" />
      <h3 className="fmtm-text-grey-700 fmtm-font-semibold">Accepting Invitation...</h3>
    </div>
  );
};

export default Invite;
