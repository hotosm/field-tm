import React, { useState } from 'react';
import Button from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import { DeleteProjectService } from '@/api/CreateProjectService';
import { useAppDispatch } from '@/types/reduxTypes';

const FormUpdateTab = ({ projectId, projectName }) => {
  const dispatch = useAppDispatch();
  const [showModal, setShowModal] = useState(false);
  const [confirmProjectName, setConfirmProjectName] = useState('');
  const [confirmEnabled, setConfirmEnabled] = useState(false);

  const onDelete = () => {
    setShowModal(true);
  };

  const onSave = () => {
    if (confirmProjectName === projectName) {
      dispatch(DeleteProjectService(`${import.meta.env.VITE_API_URL}/projects/${projectId}`));
      setShowModal(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setConfirmProjectName('');
    setConfirmEnabled(false);
  };

  const handleConfirmChange = (e) => {
    const inputText = e.target.value;
    setConfirmProjectName(inputText);
    setConfirmEnabled(inputText === projectName);
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-gap-10">
      <div className="fmtm-flex fmtm-justify-left">
        <Button variant="primary-red" onClick={onDelete}>
          DELETE PROJECT
        </Button>
      </div>
      <Modal
        className="fmtm-w-[700px]"
        description={
          <div className="text-center">
            <h5>Are you sure?</h5>
            <p>Please confirm the project name to proceed:</p>
            <input type="text" value={confirmProjectName} onChange={handleConfirmChange} />
            <div className="fmtm-flex fmtm-justify-center fmtm-gap-4">
              <Button variant="primary-red" onClick={onSave} disabled={!confirmEnabled}>
                Confirm
              </Button>
              <Button variant="secondary-red" onClick={closeModal}>
                Cancel
              </Button>
            </div>
          </div>
        }
        open={showModal}
        onOpenChange={setShowModal}
      />
    </div>
  );
};

export default FormUpdateTab;
