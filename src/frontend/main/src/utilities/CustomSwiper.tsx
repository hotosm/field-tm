import { Swiper, SwiperSlide } from 'swiper/react';

// import Swiper core and required modules

import React from 'react';
import { Box, Stack } from '@mui/material';
import { Navigation, Pagination } from "swiper";
import CustomSwiperSwitcher from './CustomSwiperSwtcher';

const CustomSwiper = ({ listOfData, switchMode, screenType }) => {

    return (
        <Stack className="App" p={3}>
            <Box marginTop={4}>
                <Swiper
                    navigation={true}
                    modules={[Pagination, Navigation]}
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
                    loopFillGroupWithBlank={true}
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
                    {listOfData.map((item, i) => (
                        <SwiperSlide key={i}>
                            <CustomSwiperSwitcher
                                data={item}
                                mode={switchMode}
                                selected={listOfData[0]}
                            />
                        </SwiperSlide>
                    ))}
                </Swiper>
            </Box>
        </Stack>
    )
}

export default CustomSwiper;