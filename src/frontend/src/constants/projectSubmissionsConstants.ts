type reviewStateDataType = { label: string; value: string };

export const reviewStateData: reviewStateDataType[] = [
  { label: 'Received', value: 'received' },
  { label: 'Has issues', value: 'hasIssues' },
  { label: 'Edited', value: 'edited' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
];
