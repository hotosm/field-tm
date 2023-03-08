import React, { useEffect } from "react";
import '../styles/login.css' 
import windowDimention from "../hooks/WindowDimension";
import { useDispatch, useSelector } from 'react-redux';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Input from '@mui/material/Input';
import Button from '@mui/material/Button';
import TextField from "@mui/material/TextField";


//import { LoginToken } from "../api/LoginService";
import enviroment from "../environment";
import Axios  from "axios";

    /*
Create a simple input element in React that calls a function when onFocusOut is triggered
*/




const Login = () => {
    // const state:any = useSelector<any>(state=>state.project.projectData)
    // console.log('state main :',state)

    const { type } = windowDimention();
    //get window dimension

    const dispatch = useDispatch()
    //dispatch function to perform redux state mutation

    const stateHome = useSelector((state: any) => state.home);
    //we use use selector from redux to get all state of home from home slice

 


    return (
        <div style={{ padding: 7 }}> 
          
            <div id="buttons">
            



   <FormControl>

<Button id="authenticate"></Button>

    <TextField
            margin="normal"
            required
            fullWidth
            id="username"
            label="Username"
            name="fmtm-username"
            autoComplete="requested username"
            />

    <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Password"
            name="fmtm-password"
            autoComplete="password"
            />


        <p>
        <a href ="/recoveraccess"><small>password recovery</small></a>
         </p>

    </FormControl>
  

    <button id="signup" className="warning">Login</button>


            </div>
            
        </div>




    )    
}






export default Login;