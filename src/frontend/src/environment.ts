export default {
  nodeEnv: process.env.NODE_ENV,
  baseApiUrl: process.env.API_URL,
  odkCentralUrl: process.env.ODK_CENTRAL_URL,
  odkCentralUser: process.env.ODK_CENTRAL_USER,
  odkCentralPass: process.env.ODK_CENTRAL_PASSWD,
  decode: (id: any) => {
    const decodeFromBase = window.atob(id);
    const binary = decodeFromBase;
    return parseInt(binary, 2);
  },
  encode: (dec) => {
    const desimaal = (dec >>> 0).toString(2);
    return window.btoa(desimaal);
  },
  tasksStatus: [
    {
      label: 'READY',
      action: [{ key: 'Start Mapping', value: 'LOCKED_FOR_MAPPING' }],
    },
    {
      label: 'LOCKED_FOR_MAPPING',
      action: [
        { key: 'Mark as fully mapped', value: 'MAPPED' },
        { key: 'Assign to someone else', value: 'READY' },
      ],
    },
    {
      label: 'MAPPED',
      action: [
        { key: 'Start Validating', value: 'LOCKED_FOR_VALIDATION' },
        { key: 'Return to Mapping', value: 'LOCKED_FOR_MAPPING' },
      ],
    },
    {
      label: 'LOCKED_FOR_VALIDATION',
      action: [
        { key: 'Confirm fully Mapped', value: 'VALIDATED' },
        { key: 'More Mapping Needed', value: 'INVALIDATED' },
      ],
    },
    { label: 'VALIDATED', action: [] },
    { label: 'INVALIDATED', action: [{ key: 'Map Again', value: 'LOCKED_FOR_MAPPING' }] },
    { label: 'BAD', action: [] },
    // "SPLIT",
    // "ARCHIVED",
  ],
  selectFormWays: [
    { id: 1, label: 'esri', value: 'esri' },
    { id: 2, label: 'bing', value: 'bing' },
    { id: 3, label: 'google', value: 'google' },
    { id: 4, label: 'topo', value: 'topo' },
  ],
  statusColors: {
    PENDING: 'gray',
    FAILED: 'red',
    RECEIVED: 'green',
    SUCCESS: 'green',
  },
};
