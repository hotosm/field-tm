import { Stack } from "@mui/material";
import { spacing } from "@mui/system";
import React from "react"


const CustomPwComponents = ({ element, componentData, viewMode, mainComponentStyles, spacing }) => {

    let newComponentData = componentData;
    // initialization of new project data array for further manipulations

    let componentPerRow: any = new Array(viewMode).fill(0);
    //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array

    let totalRows: any = new Array(componentData.length % componentPerRow.length == 0 ? Math.floor(componentData.length / componentPerRow.length) : Math.floor(componentData.length / componentPerRow.length) + 1).fill(0)
    //calculating number of rows that current displayed list will fit in respectively and then convert it into dummy array

    return (
        <Stack direction={'column'} spacing={2} style={mainComponentStyles}>
            {
                totalRows.map((val, index) => {
                    return (

                        <Stack direction={'row'} spacing={spacing} style={{ width: '100%', }}>
                            {
                                componentData.length % componentPerRow.length == 0 ?
                                    //checking if project list fit a defined row


                                    componentPerRow.map((val, index) => {
                                        //displaying cards on every give row
                                        let value = newComponentData.shift()
                                        //manipulating the new project array, capture current last index value, displaying it then remove it from the array 
                                        return (element)
                                    }) :


                                    //if false the we expect that there will be a reminder in our list that doesn't fit in given.
                                    //eg: list of 10 / 7 as window dimention of xl to fit our cards respectively then the reminder will be 3 which should be render in the last row
                                    index + 1 != totalRows.length ?


                                        //checking if is not the last irritation we don't focus on the reminder
                                        componentPerRow.map((val, index) => {

                                            let value = newComponentData.shift()
                                            return (element)
                                        }) :


                                        //if is the last row then we dont want to loop down the card more then the reminder
                                        // so if 3 is a reminder we only want 3 irritation to finish the last row
                                        new Array(componentData.length % componentPerRow.length).fill(0).map((val, index) => {

                                            //getting the reminder and convert it in a dummy array to get a respective loop
                                            let value = newComponentData.shift()

                                            return (element)
                                        })
                            }

                        </Stack>

                    )
                })
            }
        </Stack>
    )


}

export default CustomPwComponents;