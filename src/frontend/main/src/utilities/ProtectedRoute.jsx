import { Navigate } from 'react-router-dom';
import React from 'react';
import CoreModules from '../shared/CoreModules';
import { createLoginWindow } from '../utilfunctions/login';

const ProtectedRoute = ({ children }) => {
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  if (token == null) {
    createLoginWindow('/');
    return <Navigate to="/" replace />;
  }
  return children;
};
export default ProtectedRoute;
