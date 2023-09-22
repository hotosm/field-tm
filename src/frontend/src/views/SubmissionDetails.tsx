import CoreModules from '../shared/CoreModules.js';
import React, { useEffect } from 'react';
import environment from '../environment';
import { SubmissionService } from '../api/Submission';

const SubmissionDetails = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const encodedProjectId = params.projectId;
  const decodedProjectId = environment.decode(encodedProjectId);
  const encodedTaskId = params.taskId;
  const decodedTaskId = environment.decode(encodedTaskId);
  const paramsInstanceId = params.instanceId;

  const submissionDetails = CoreModules.useAppSelector((state) => state.submission.submissionDetails);

  useEffect(() => {
    dispatch(
      SubmissionService(
        `${environment.baseApiUrl}/central/submission?project_id=${decodedProjectId}&xmlFormId=${decodedTaskId}&submission_id=${paramsInstanceId}`,
      ),
    );
  }, []);

  function removeNullValues(obj) {
    const newObj = {};
    for (const [key, value] of Object.entries(obj)) {
      if (value !== null) {
        if (typeof value === 'object') {
          const nestedObj = removeNullValues(value);
          if (Object.keys(nestedObj).length > 0) {
            newObj[key] = nestedObj;
          }
        } else {
          newObj[key] = value;
        }
      }
    }
    return newObj;
  }
  const filteredData = removeNullValues(submissionDetails);

  const renderValue = (value) => {
    if (typeof value === 'object') {
      return (
        <ul>
          {Object.entries(value).map(([key, nestedValue]) => (
            <CoreModules.Box sx={{ textTransform: 'capitalize' }} key={key}>
              <strong color="error">{key}: </strong>
              {renderValue(nestedValue)}
            </CoreModules.Box>
          ))}
        </ul>
      );
    } else {
      return <span>{value}</span>;
    }
  };

  return (
    <CoreModules.Box
      sx={{ display: 'flex', m: '4rem', border: '1px solid gray', flexDirection: 'column', flex: 1, p: '1rem' }}
    >
      <div>
        {Object.entries(filteredData).map(([key, value]) => (
          <div key={key}>
            <CoreModules.Box sx={{ borderBottom: '1px solid #e2e2e2', padding: '8px' }}>
              <CoreModules.Typography variant="h1" sx={{ textTransform: 'capitalize' }}>
                {key}
              </CoreModules.Typography>
              {renderValue(value)}
            </CoreModules.Box>
          </div>
        ))}
      </div>
    </CoreModules.Box>
  );
};

export default SubmissionDetails;
