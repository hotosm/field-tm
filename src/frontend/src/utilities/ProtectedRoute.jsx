import React from 'react';
import axios from 'axios';
import { Navigate, useLocation } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules';
import { LoginActions } from '@/store/slices/LoginSlice';
import Forbidden from '@/views/Forbidden';

const ProtectedRoute = ({ children, next }) => {
  const dispatch = CoreModules.useAppDispatch();
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const { pathname, search } = useLocation();
  const [isForbidden, setIsForbidden] = React.useState(false);

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response ? error.response.status : null;

      if (status === 403) {
        setIsForbidden(true);
      }
      return Promise.reject(error);
    },
  );

  if (isForbidden) return <Forbidden />;

  if (authDetails == null) {
    dispatch(LoginActions.setLoginModalOpen(true));
    return <Navigate to="/" replace state={{ from: `${pathname}${search}` }} />;
  }

  return children;
};
export default ProtectedRoute;
