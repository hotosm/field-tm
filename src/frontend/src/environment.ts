export default {
  decode: (id: any) => {
    const decodeFromBase = window.atob(id);
    const binary = decodeFromBase;
    return parseInt(binary, 2);
  },
  encode: (dec) => {
    const decimal = (dec >>> 0).toString(2);
    return window.btoa(decimal);
  },
  matomoTrackingId: '28',
  tasksStatus: [
    {
      label: 'UNLOCKED_TO_MAP',
      action: [{ key: 'Assign To Mapper', value: 'MAP', btnBG: 'red' }],
      btnBG: 'red',
    },
    {
      label: 'LOCKED_FOR_MAPPING',
      action: [
        { key: 'Mark as fully mapped', value: 'FINISH', btnBG: 'gray' },
        { key: 'Stop Mapping', value: 'BAD', btnBG: 'transparent' },
      ],
    },
    {
      label: 'UNLOCKED_TO_VALIDATE',
      action: [
        { key: 'Start Validation', value: 'VALIDATE', btnBG: 'gray' },
        { key: 'Reset', value: 'BAD' },
      ],
    },
    {
      label: 'LOCKED_FOR_VALIDATION',
      action: [
        { key: 'Mark As Validated', value: 'GOOD', btnBG: 'gray' },
        { key: 'Mapping Needed', value: 'BAD', btnBG: 'transparent' },
      ],
    },
    {
      label: 'UNLOCKED_DONE',
      action: [
        { key: 'Reset', value: 'BAD', btnBG: 'gray' },
        // { key: 'Merge data with OSM', value: 'CONFLATE', btnBG: 'gray' },
      ],
    },
    // TODO add SPLIT, MERGE, ASSIGN
  ],
  baseMapProviders: [
    { id: 1, label: 'ESRI', value: 'esri' },
    { id: 2, label: 'Bing', value: 'bing' },
    { id: 3, label: 'Google', value: 'google' },
    { id: 5, label: 'Custom TMS', value: 'custom' },
  ],
  tileOutputFormats: [
    { id: 1, label: 'MBTiles', value: 'mbtiles' },
    { id: 2, label: 'OSMAnd', value: 'sqlitedb' },
    { id: 3, label: 'PMTiles', value: 'pmtiles' },
  ],
  statusColors: {
    PENDING: 'gray',
    FAILED: 'red',
    RECEIVED: 'green',
    SUCCESS: 'green',
  },
};
