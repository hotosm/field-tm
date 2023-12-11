export default {
  decode: (id: any) => {
    const decodeFromBase = window.atob(id);
    const binary = decodeFromBase;
    return parseInt(binary, 2);
  },
  encode: (dec) => {
    const desimaal = (dec >>> 0).toString(2);
    return window.btoa(desimaal);
  },
  mamotoTrackingId: 28,
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
  baseMapProviders: [
    { id: 1, label: 'ESRI', value: 'esri' },
    { id: 2, label: 'Bing', value: 'bing' },
    { id: 3, label: 'Google', value: 'google' },
    { id: 4, label: 'Topo', value: 'topo' },
    { id: 5, label: 'Custom TMS', value: 'tms' },
  ],
  tileOutputFormats: [
    { id: 1, label: 'MBTiles', value: 'mbtiles' },
    { id: 2, label: 'OSMAnd', value: 'sqlite3' },
    { id: 3, label: 'PMTiles', value: 'pmtiles' },
  ],
  statusColors: {
    PENDING: 'gray',
    FAILED: 'red',
    RECEIVED: 'green',
    SUCCESS: 'green',
  },
};
