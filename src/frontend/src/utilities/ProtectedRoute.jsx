import { Navigate } from 'react-router-dom';
import React from 'react';
import CoreModules from '../shared/CoreModules';
import { createLoginWindow } from '../utilfunctions/login';
import environment from '../environment';

const ProtectedRoute = ({ children }) => {
  // Bypass check if NODE_ENV=development (local dev)
  if (import.meta.env.MODE === 'development') {
    return children;
  }

  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  if (token == null) {
    createLoginWindow('/');
    return <Navigate to="/" replace />;
  }
  return children;
};
export default ProtectedRoute;
