import * as React from 'react';
import clsx from 'clsx';
import { styled, Box, Theme } from '@mui/system';
import { Modal } from '@mui/base/Modal';

type customizeModal = {
  style: Record<string, any>;
  children: React.ReactNode;
  isOpen: boolean;
  toggleOpen: (flag: boolean) => void;
};

export default function CustomizedModal({ style = defaultStyle, children, isOpen, toggleOpen }: customizeModal) {
  const handleClose = () => toggleOpen(false);

  return (
    <div>
      <StyledModal
        aria-labelledby="unstyled-modal-title"
        aria-describedby="unstyled-modal-description"
        open={isOpen}
        onClose={handleClose}
        slots={{ backdrop: StyledBackdrop }}
      >
        <Box sx={style}>{React.Children.only(children)}</Box>
      </StyledModal>
    </div>
  );
}

interface BackdropProps extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean;
}

const Backdrop: React.FC<BackdropProps> = ({ open, className, ref, ...other }) => {
  return <div className={clsx({ 'MuiBackdrop-open': open }, className)} ref={ref} {...other} />;
};
Backdrop.displayName = 'ModalBackdrop';

const StyledModal = styled(Modal)`
  position: fixed;
  z-index: 1300;
  right: 0;
  bottom: 0;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const StyledBackdrop = styled(Backdrop)`
  z-index: -1;
  position: fixed;
  right: 0;
  bottom: 0;
  top: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.5);
  -webkit-tap-highlight-color: transparent;
`;

const defaultStyle = (theme: Theme) => ({
  width: '80%',
  height: '80%',
  bgcolor: theme.palette.mode === 'dark' ? '#0A1929' : 'white',
  border: '1px solid ',
  borderRadius: '10px',
  padding: '16px 32px 24px 32px',
});
