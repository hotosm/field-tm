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
  matomoTrackingId: '28',
  tasksStatus: [
    {
      label: 'RELEASED_FOR_MAPPING',
      action: [{ key: 'Start Mapping', value: 'LOCKED_FOR_MAPPING', btnBG: 'red' }],
      btnBG: 'red',
    },
    {
      label: 'LOCKED_FOR_MAPPING',
      action: [
        { key: 'Mark as fully mapped', value: 'MARKED_MAPPED', btnBG: 'gray' },
        { key: 'Stop Mapping', value: 'RELEASED_FOR_MAPPING', btnBG: 'transparent' },
      ],
    },
    {
      label: 'MARKED_MAPPED',
      action: [
        { key: 'Start Validation', value: 'LOCKED_FOR_VALIDATION', btnBG: 'gray' },
        // { key: 'Return to Mapping', value: 'LOCKED_FOR_MAPPING' },
      ],
    },
    {
      label: 'LOCKED_FOR_VALIDATION',
      action: [
        { key: 'Mark as validated', value: 'VALIDATED', btnBG: 'gray' },
        { key: 'Mapping Needed', value: 'MARKED_INVALID', btnBG: 'transparent' },
      ],
    },
    { label: 'VALIDATED', action: [] },
    // { label: 'VALIDATED', action: [{ key: 'Merge data with OSM', value: 'MERGE_WITH_OSM', btnBG: 'gray' }] },
    { label: 'MARKED_INVALID', action: [{ key: 'Map Again', value: 'LOCKED_FOR_MAPPING', btnBG: 'gray' }] },
    { label: 'MARKED_BAD', action: [] },
    // "SPLIT",
    // "ARCHIVED",
  ],
  baseMapProviders: [
    { id: 1, label: 'ESRI', value: 'esri' },
    { id: 2, label: 'Bing', value: 'bing' },
    { id: 3, label: 'Google', value: 'google' },
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
