import React, { useEffect, useState } from "react";
// Extra small.col -    < 576px	Mobile Display
// Small.col - sm - ≥576px	Mobile Display
// Medium.col - md - ≥768px	Tablet Display
// Large.col - lg -  ≥992px	Desktop Display
// Extra large.col - xl - ≥1200px Desktop Display
function calculateWidthType(width) {
    if (width >= 1700) {
        return 'xl'
    }
    else if (width >= 1332) {
        return 'lg'
    }
    else if (width >= 1200) {
        return 'md'
    } else if (width >= 855) {
        return 'sm'
    } else if (width >= 632) {
        return 's'
    } else if (width < 632) {
        return 'xs'
    }
}

const windowDimention = () => {
    const [windowSize, setWindowSize] = useState({
        width: 0,
        height: 0
    })



    useEffect(() => {
        const handleResize = () => {
            setWindowSize({
                width: window.innerWidth,
                height: window.innerHeight
            })
        }

        handleResize();

        window.addEventListener('resize', handleResize)

        const cleanUp = () => {
            window.removeEventListener('resize', handleResize)
        }

        return cleanUp;
    }, [])

    return { windowSize, type: calculateWidthType(windowSize.width) };




}


export default windowDimention;