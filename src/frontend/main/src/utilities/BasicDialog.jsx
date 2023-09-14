import * as React from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
export default function BasicDialog({ open, actions, title, onClose, subtitle }) {
  return (
    <CoreModules.Dialog fullWidth open={open}>
      <CoreModules.Stack position={'absolute'} right={'1.5%'} top={'1.5%'} borderRadius={60} height={50} width={40}>
        <CoreModules.IconButton onClick={onClose}>
          <AssetModules.CloseIcon color="info" />
        </CoreModules.IconButton>
      </CoreModules.Stack>
      <CoreModules.Stack direction={'column'} spacing={2}>
        {title != undefined ? (
          <CoreModules.Stack p={1} direction={'row'} pl={3}>
            <CoreModules.Typography variant="h2" mt={'3%'} fontSize={20}>
              {title}
            </CoreModules.Typography>
          </CoreModules.Stack>
        ) : null}
        {subtitle != undefined ? (
          <CoreModules.Stack direction={'row'} pl={3}>
            <CoreModules.Typography variant="h3">{subtitle}</CoreModules.Typography>
          </CoreModules.Stack>
        ) : null}
      </CoreModules.Stack>
      <CoreModules.Stack justifyContent={'center'} p={2}>
        {actions}
      </CoreModules.Stack>
    </CoreModules.Dialog>
  );
}
