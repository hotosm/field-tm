import { Navigate } from 'react-router-dom';
import React from 'react';
import CoreModules from '@/shared/CoreModules';
import { createLoginWindow } from '@/utilfunctions/login';
import environment from '@/environment';

const ProtectedRoute = ({ children }) => {
  // Bypass check if NODE_ENV=development (local dev)
  if (import.meta.env.MODE === 'development') {
    return children;
  }
  console.log(import.meta.env,'test');
  // const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const changedDomainToUnderscore = import.meta.env.VITE_FMTM_DOMAIN.replace('.', '_');
  const token = getCookie(changedDomainToUnderscore);
  if (token == null) {
    createLoginWindow('/');
    return <Navigate to="/" replace />;
  }
  return children;
};
export default ProtectedRoute;
