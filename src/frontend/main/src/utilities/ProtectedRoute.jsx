import { Navigate } from 'react-router-dom';
import React from 'react';
import CoreModules from '../shared/CoreModules';
const ProtectedRoute = ({ children }) => {
  const token = CoreModules.useSelector((state) => state.login.loginToken);
  if (token == null) {
    return <Navigate to="/login" replace />;
  }
  return children;
};
export default ProtectedRoute;
