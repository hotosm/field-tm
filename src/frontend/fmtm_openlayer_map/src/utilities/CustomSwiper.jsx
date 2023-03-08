import { Swiper, SwiperSlide } from 'swiper/react';

// import Swiper core and required modules

import React, { useEffect, useState } from 'react';
import { Box, Button, Stack } from '@mui/material';
import { Navigation, Pagination } from "swiper";


const CustomSwiper = ({ listOfData, defaultTheme, screenType, onClick, selected, loading }) => {
    const [list, setListOfData] = useState([])
    useEffect(() => {
        setListOfData(listOfData)
    }, [])


    return (
        <Stack className="App" >
            <Box marginTop={4}>
                <Swiper
                    navigation={true}
                    modules={[Navigation]}
                    slidesPerView={
                        screenType == 'sm' ? 4 :
                            screenType == 's' ? 2 :
                                screenType == 'xs' ? 2 : 6
                    }
                    spaceBetween={40}
                    slidesPerGroup={
                        screenType == 'sm' ? 4 :
                            screenType == 's' ? 2 :
                                screenType == 'xs' ? 2 : 6
                    }
                    loop={true}

                    pagination={{
                        clickable: true,
                    }}
                    style={{
                        paddingLeft: 40,
                        paddingRight: 40,
                        paddingBottom: 40,
                        paddingTop: 38
                    }}
                >
                    {list.map((item, index) => {
                        return (
                            <SwiperSlide key={index}>
                                <Button
                                    key={index}
                                    color="error"
                                    id={item.id}
                                    disabled={loading}
                                    style={{
                                        fontSize: defaultTheme.typography.htmlFontSize,
                                        fontFamily: defaultTheme.typography.h3.fontFamily,
                                    }}
                                    onClick={onClick}
                                    variant={selected == item.id ? 'contained' : 'outlined'}
                                >
                                    {`Task #${item.id}`}
                                </Button>
                            </SwiperSlide>
                        )
                    })}
                </Swiper>
            </Box>
        </Stack>
    )
}

export default CustomSwiper;
