import React, { useState, useCallback } from 'react';
import '../styles/login.css';
import enviroment from '../environment';
import CoreModules from '../shared/CoreModules';
import { SignUpService } from '../api/LoginService';
import { SingUpModel } from '../models/login/loginModel';
/*
Create a simple input element in React that calls a function when onFocusOut is triggered
*/

const Create = () => {
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const token: any = CoreModules.useAppSelector((state) => state.login.loginToken);
  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation
  const navigate = CoreModules.useNavigate();
  const initalUserForm = {
    username: '',
    password: '',
    confirmPassword: '',
  };
  const [userForm, setUserForm] = useState<any>(initalUserForm);
  const btnStyles = {
    padding: 8,
    width: '100%',
    borderRadius: 7,
    fontFamily: defaultTheme.typography.subtitle2.fontFamily,
  };
  const handleOnChange = (e) => {
    const value = e.target.value;
    const name = e.target.name;
    setUserForm((prev) => {
      const newValues = { ...prev };
      newValues[name] = value;
      return newValues;
    });
  };

  const handleOnSubmit = useCallback(async () => {
    const body: SingUpModel = { ...userForm };
    setUserForm(initalUserForm);
    await dispatch(SignUpService(`${enviroment.baseApiUrl}/users/`, body));
    setTimeout(() => {
      navigate('/login');
    }, 500);
  }, [initalUserForm]);

  return (
    <CoreModules.Stack direction={'row'} justifyContent={'center'}>
      <CoreModules.Stack width={600} p={2} spacing={2}>
        <CoreModules.Stack direction={'row'} justifyContent={'center'}>
          <CoreModules.Typography variant="subtitle1">CREATE ACCOUNT</CoreModules.Typography>
        </CoreModules.Stack>
        <CoreModules.TextField
          color="info"
          fullWidth
          id="filled-basic"
          label="Username"
          variant="filled"
          name="username"
          onChange={handleOnChange}
          value={userForm.username}
        />
        <CoreModules.TextField
          color="info"
          fullWidth
          id="filled-basic"
          label="Password"
          variant="filled"
          name="password"
          type={'password'}
          onChange={handleOnChange}
          value={userForm.password}
        />
        <CoreModules.TextField
          color="info"
          fullWidth
          id="filled-basic"
          label="Confirm Password"
          variant="filled"
          name="confirmPassword"
          type={'password'}
          onChange={handleOnChange}
          value={userForm.confirmPassword}
        />
        <CoreModules.Button
          onClick={handleOnSubmit}
          style={btnStyles}
          disabled={token != null}
          color="error"
          variant="contained"
        >
          sign up
        </CoreModules.Button>
        <CoreModules.Typography>
          Already have an account ?{' '}
          <CoreModules.Link style={{ textDecoration: 'none' }} to={'/login'}>
            Sign in
          </CoreModules.Link>
        </CoreModules.Typography>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default Create;
