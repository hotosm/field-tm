import React from 'react';
import { Navigate } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules';
import { LoginActions } from '@/store/slices/LoginSlice';

const ProtectedRoute = ({ children, next }) => {
  const dispatch = CoreModules.useAppDispatch();
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  if (authDetails == null) {
    dispatch(LoginActions.setLoginModalOpen(true));
    return <Navigate to="/" replace />;
  }

  return children;
};
export default ProtectedRoute;
