import React from "react";
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton'

const ProjectCardSkeleton = ({ cardsPerRow }) => {
    return (

        cardsPerRow.map((data, index) => {
            return (
                <div key={index} style={{ width: `${100 / cardsPerRow.length}%`, padding: 3, border: '1px solid lightgray', marginTop: '1%', marginLeft: '0.1%', marginRight: '0.1%', height: 'inherit' }}>

                    <div className="row mt-2">
                        <div className="col-md-12">
                            <Skeleton style={{ marginTop: '3%', float: 'right', width: 69 }} count={1} />
                        </div>
                        <div className="col-md-4 mt-1">
                            <Skeleton height={25} />
                        </div>
                        <div className="col-md-4">

                        </div>
                        <div className="col-md-4 mt-1">
                            <Skeleton height={25} />
                        </div>
                        <div className="col-md-12">
                            <Skeleton style={{ marginTop: '4%' }} height={20} />

                            <Skeleton style={{ marginTop: '4%' }} height={170} />
                        </div>
                        <div className="col-md-12 mt-2">
                            <Skeleton style={{ marginTop: '3%' }} height={12} count={2} />
                        </div>
                    </div>
                </div>

            )
        })
    )
}
export default ProjectCardSkeleton;