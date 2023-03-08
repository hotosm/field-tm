import React, { useEffect } from "react";
import '../styles/login.css' 
import windowDimention from "../hooks/WindowDimension";
import { useDispatch, useSelector } from 'react-redux';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Input from '@mui/material/Input';
import TextField from "@mui/material/TextField";
import Button from '@mui/material/Button';


/// import { LoginSummaryService } from "../api/LoginService";
import enviroment from "../environment";
import Axios  from "axios";



const Forgot = () => {
    // const state:any = useSelector<any>(state=>state.project.projectData)
    // console.log('state main :',state)

    const { type } = windowDimention();
    //get window dimension

    const dispatch = useDispatch()
    //dispatch function to perform redux state mutation

    const stateLogin = useSelector((state: any) => state.login);
    //we use use selector from redux to get all state of token from login slice

 



    return (
        <div style={{ padding: 7 }}> 
          
            <div id="buttons">
            
 
                <FormControl>

                <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="email"
                        label="Email Address"
                        name="email"
                        autoComplete="email"
                        autoFocus
                        />

                <TextField
                        margin="normal"
                        required
                        fullWidth
                        id=""
                        label="User Name"
                        name="fmtm-username"
                        autoComplete="requested username"
                        autoFocus
                        />
                
                <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="fmtm-mobile"
                        label="Mobile Number"
                        name="fmtm-mobile"
                        autoComplete="###-###-####"
                        autoFocus
                        />

                <Button id="authenticate">Request Password</Button>


                </FormControl>
            

                <button id="submit">Send a link</button>


            </div>
            
        </div>


    )    
}


export default Forgot;