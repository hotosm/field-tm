import CoreModules from '../shared/CoreModules.js';
import React, { useEffect } from 'react';
import environment from '../environment';
import { SubmissionService } from '../api/Submission';

function process_data(data) {
    let result = '';
    for (let key in data) {
        if (data.hasOwnProperty(key) && data[key] !== null) {
            if (typeof data[key] === 'object' && data[key] !== null) {
                result += `<h2>${key}</h2>`;
                result += process_data(data[key]);
            } else {
                result += `<h4>${key}: ${data[key]}</h4>`;
            }
        }
    }
    return result;
}

const SubmissionDetails = props => {
    const dispatch = CoreModules.useDispatch();
    const params = CoreModules.useParams();
    const encodedProjectId = params.projectId;
    const decodedProjectId = environment.decode(encodedProjectId);
    const encodedTaskId = params.taskId;
    const decodedTaskId = environment.decode(encodedTaskId);
    const paramsInstanceId = params.instanceId;

    const submissionDetails = CoreModules.useSelector((state) => state.submission.submissionDetails);

    useEffect(() => {
        dispatch(SubmissionService(`${environment.baseApiUrl}/central/submission?project_id=${decodedProjectId}&xmlFormId=${decodedTaskId}&submission_id=${paramsInstanceId}`))
    }, [])


    return (
        <CoreModules.Box sx={{ display: 'flex', m: '4rem', border: '1px solid gray', flexDirection: 'column' }}>
            <div dangerouslySetInnerHTML={{ __html: process_data(submissionDetails) }}></div>
            {/* {Object.entries(submissionDetails).map(([key, value]) => {
                if (typeof value === 'object' && value !== null) {
                    return Object.entries(value).map(([key2, value2]) => {
                        if (typeof value2 === 'object' && value2 !== null) {
                            return Object.entries(value2).map(([key3, value3]) => <CoreModules.Stack sx={{ p: '1rem' }}>
                                <h3>{key3}</h3>
                                <h4 style={{ backgroundColor: 'red' }}>{value3}</h4>
                            </CoreModules.Stack>)
                        } else {
                            return <CoreModules.Stack sx={{ p: '1rem' }}>
                                <h3>{key2}</h3>
                                <h4 style={{ backgroundColor: 'red' }}>{value2}</h4>
                            </CoreModules.Stack>

                        }
                    })
                } else {
                    return <CoreModules.Stack sx={{ p: '1rem' }}>
                        <h3>{key}</h3>
                        <h4 style={{ backgroundColor: 'red' }}>{value}</h4>
                    </CoreModules.Stack>

                }
            })} */}
        </CoreModules.Box>
    )
}


export default SubmissionDetails