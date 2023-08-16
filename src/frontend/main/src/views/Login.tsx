import React, { useEffect, useState } from 'react';
import '../styles/login.css';
import enviroment from '../environment';
import CoreModules from '../shared/CoreModules';
import { SignInService } from '../api/LoginService';
import { useCallback } from 'react';
import { SingUpModel } from '../models/login/loginModel';

/*
Create a simple input element in React that calls a function when onFocusOut is triggered
*/

const Login = () => {
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const navigate = CoreModules.useNavigate();
  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation
  const token: any = CoreModules.useAppSelector((state) => state.login.loginToken);
  // console.log(location.pathname,'and :',token);
  const initalUserForm = {
    username: '',
    password: '',
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

  useEffect(() => {
    if (token != null) {
      setTimeout(() => {
        navigate('/');
      }, 500);
    }
  }, [token]);

  const handleOnSubmit = useCallback(async () => {
    const body: SingUpModel = { ...userForm };
    setUserForm(initalUserForm);
    await dispatch(SignInService(`${enviroment.baseApiUrl}/users/`, body));
  }, [initalUserForm]);

  return (
    <CoreModules.Stack direction={'row'} justifyContent={'center'}>
      <CoreModules.Stack width={600} p={2} spacing={2}>
        <CoreModules.Stack direction={'row'} justifyContent={'center'}>
          <CoreModules.Typography variant="subtitle1">SIGN IN</CoreModules.Typography>
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
        <CoreModules.Button onClick={handleOnSubmit} style={btnStyles} color="error" variant="contained">
          sign in
        </CoreModules.Button>
        <CoreModules.Typography>
          don&apos;t have an account ?{' '}
          <CoreModules.Link style={{ textDecoration: 'none' }} to={'/signup'}>
            Sign up
          </CoreModules.Link>
        </CoreModules.Typography>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default Login;
