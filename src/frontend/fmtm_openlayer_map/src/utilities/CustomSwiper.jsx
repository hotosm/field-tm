
// import Swiper core and required modules
import React, { useEffect, useState } from 'react';
import CoreModules from 'fmtm/CoreModules';


const CustomSwiper = ({ listOfData, defaultTheme, screenType, onClick, selected, loading }) => {
    const [list, setListOfData] = useState([])
    useEffect(() => {
        setListOfData(listOfData)
    }, [])


    return (
        <CoreModules.Stack className="App" >
            <CoreModules.Stack direction={'row'} marginTop={4}>
                <CoreModules.Swiper
                    navigation={true}
                    modules={[CoreModules.SwiperNavigation]}
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
                            <CoreModules.SwiperSlide key={index}>
                                <CoreModules.Button
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
                                </CoreModules.Button>
                            </CoreModules.SwiperSlide>
                        )
                    })}
                </CoreModules.Swiper>
            </CoreModules.Stack>
        </CoreModules.Stack>
    )
}

export default CustomSwiper;
