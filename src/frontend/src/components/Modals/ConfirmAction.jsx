import React from 'react';
import {
  ComposedModal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
} from '@carbon/react';

export default function ConfirmAction({
  open = false,
  title = 'Confirm Action',
  description = 'Are you sure you want to proceed?',
  onConfirm,
  onClose,
  isDanger = false,
}) {
  return (
    <ComposedModal open={open} onClose={onClose} size="sm">
      <ModalHeader title={title} />
      <ModalBody>
        <p style={{ fontSize: '14px', color: '#525252', lineHeight: '1.5' }}>
          {description}
        </p>
      </ModalBody>
      <ModalFooter>
        <Button kind="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button kind={isDanger ? 'danger' : 'primary'} onClick={onConfirm}>
          Confirm
        </Button>
      </ModalFooter>
    </ComposedModal>
  );
}
