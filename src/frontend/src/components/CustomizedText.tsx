import React from "react";


const CustomizedText = ({text,size,font,weight,top})=>{

    return(
        <span style={{fontSize:size,fontFamily:font,fontWeight:weight,marginTop:top}}>{text}</span>
    )
}

export default CustomizedText;