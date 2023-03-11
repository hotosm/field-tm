import React from "react";
import CoreModules from '../../shared/CoreModules';
// Skeleton card main purpose is to perfom loading in case of any delay in retrieving project
const ProjectCardSkeleton = ({ cardsPerRow, defaultTheme }) => {

    return (

        cardsPerRow.map((data, index) => {
            return (
                <div key={index} style={{ width: `${100 / cardsPerRow.length}%`, padding: 3, border: '1px solid lightgray', marginTop: '1%', marginLeft: '0.1%', marginRight: '0.1%', height: 'inherit' }}>

                    <div className="row mt-2">
                        <div className="col-md-12">


                            <CoreModules.SkeletonTheme
                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                            >
                                <CoreModules.Skeleton
                                    width={69}
                                    style={{ marginTop: '3%', float: 'right' }}
                                    count={1}
                                />
                            </CoreModules.SkeletonTheme>
                        </div>
                        <div className="col-md-4 mt-1">
                            <CoreModules.SkeletonTheme
                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                            >
                                <CoreModules.Skeleton height={25} />
                            </CoreModules.SkeletonTheme>
                        </div>
                        <div className="col-md-4">

                        </div>
                        <div className="col-md-4 mt-1">
                            <CoreModules.SkeletonTheme
                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                            >
                                <CoreModules.Skeleton height={25} />
                            </CoreModules.SkeletonTheme>
                        </div>
                        <div className="col-md-12">
                            <CoreModules.SkeletonTheme
                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                            >
                                <CoreModules.Skeleton style={{ marginTop: '7%' }} height={23} />
                                <CoreModules.Skeleton style={{ marginTop: '4%' }} height={16} />
                                <CoreModules.Skeleton style={{ marginTop: '5%' }} height={90} />
                            </CoreModules.SkeletonTheme>

                        </div>
                        <div className="col-md-12 mt-2">
                            <CoreModules.SkeletonTheme
                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                            >
                                <CoreModules.Skeleton style={{ marginTop: '1%' }} height={12} count={2} />
                            </CoreModules.SkeletonTheme>
                        </div>
                    </div>
                </div>

            )
        })
    )
}
export default ProjectCardSkeleton;