import React from 'react';
import CoreModules from '@/shared/CoreModules';
import { DeleteProjectService } from '@/api/CreateProjectService';

const DeleteProject = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(DeleteProjectService(`/projects/${projectId}`));
  };

  return (
    <form onSubmit={handleSubmit}>
      <CoreModules.Stack flexDirection="row">
        <CoreModules.Stack sx={{ width: '45%' }}>
          <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
            <CoreModules.LoadingButton
              // disabled={updateBoundaryLoading}
              type="submit"
              // loading={updateBoundaryLoading}
              loadingPosition="end"
              // endIcon={<AssetModules.SettingsSuggestIcon />}
              variant="contained"
              color="error"
            >
              Delete
            </CoreModules.LoadingButton>
          </CoreModules.Stack>
        </CoreModules.Stack>
      </CoreModules.Stack>
    </form>
  );
};

export default DeleteProject;
