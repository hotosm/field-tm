import React from "react";
import cardImg from '../images/project_icon.png';
import logo from '../images/hotLog.png'
const CustomizedImage = ({ status, style }) => {
    return (
        <div>
            {
                status == 'card' ?
                    <img src={cardImg} style={style} />
                    : status == 'logo' ?
                        <img src={logo} style={style} />
                        : null
            }
        </div>
    )
}

export default CustomizedImage;