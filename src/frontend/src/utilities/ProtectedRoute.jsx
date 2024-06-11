import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules';
import { LoginActions } from '@/store/slices/LoginSlice';

const ProtectedRoute = ({ children, next }) => {
  const dispatch = CoreModules.useAppDispatch();
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const { pathname } = useLocation();

  if (authDetails == null) {
    dispatch(LoginActions.setLoginModalOpen(true));
    return <Navigate to="/" replace state={{ from: pathname }} />;
  }

  return children;
};
export default ProtectedRoute;
