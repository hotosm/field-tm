import React, { useEffect } from "react";
import '../styles/login.css' 
import windowDimention from "../hooks/WindowDimension";
import { useDispatch, useSelector } from 'react-redux';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Input from '@mui/material/Input';
import Button from '@mui/material/Button';
import TextField from "@mui/material/TextField";


import { LoginSummaryService } from "../api/LoginService";
import enviroment from "../environment";
import Axios  from "axios";

    /*
Create a simple input element in React that calls a function when onFocusOut is triggered
*/




const Create = () => {
    // const state:any = useSelector<any>(state=>state.project.projectData)
    // console.log('state main :',state)

    const { type } = windowDimention();
    //get window dimension

    const dispatch = useDispatch()
    //dispatch function to perform redux state mutation

    const stateHome = useSelector((state: any) => state.home);
    //we use use selector from redux to get all state of home from home slice



    useEffect(() => {
        dispatch(LoginSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
        //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    }, [])

    return (
        <div style={{ padding: 7 }}>

            <div id="buttons">




   <FormControl>



                <TextField
                        margin="normal"
                        fullWidth
                        id="username"
                        label="User Name"
                        name="fmtm-username"
                        autoComplete="requested username"
                        autoFocus
                        />

                <TextField
                        margin="normal"
                        fullWidth
                        id="email"
                        label="Email Address"
                        name="email"
                        autoComplete="email"
                        autoFocus
                        />

                <TextField
                        margin="normal"
                        fullWidth
                        id="mobile"
                        label="Mobile Number"
                        name="mobile"
                        autoComplete="###-###-####"
                        autoFocus
                        />

      <a href ="/recoveraccess">forgot passord</a>


    </FormControl>


    <button id="signup" >Sign Up</button>


            </div>

        </div>
    )
}

export default Create;
