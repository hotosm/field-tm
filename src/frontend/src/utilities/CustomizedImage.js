import React from "react";
import cardImg from '../assets/images/project_icon.png';
import logo from '../assets/images/hotLog.png'

const Switcher = ({ status, style }) => {
    switch (status) {
        case 'card':
            return <img src={cardImg} style={style} />
        case 'logo':
            return <img src={logo} style={style} />

    }
}

const CustomizedImage = ({ status, style }) => {
    return (
        <Switcher status={status} style={style} />
    )
}

export default CustomizedImage;