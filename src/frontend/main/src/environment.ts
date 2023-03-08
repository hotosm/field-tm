export default {
  baseApiUrl: process.env.API_URL,
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
    { key: 'READY', value: ["LOCKED_FOR_MAPPING", "BAD"], action: 'none', status: 2 },
    { key: 'LOCKED_FOR_MAPPING', value: ["READY", "MAPPED", "BAD"], action: 'qrcode', status: 1 },
    { key: 'MAPPED', value: ["LOCKED_FOR_MAPPING", "LOCKED_FOR_VALIDATION", "BAD"], actin: 'none', status: 3 },
    { key: 'LOCKED_FOR_VALIDATION', value: ["VALIDATED", "INVALIDATED", "BAD"], action: 'submissions', status: 4 },
    { key: 'VALIDATED', value: [], action: 'none', status: 5 },
    { key: 'INVALIDATED', value: ["LOCKED_FOR_MAPPING", "BAD"], action: 'none', status: 7 },
    { key: 'BAD', value: [], action: 'none', status: 6 },
    // "SPLIT",
    // "ARCHIVED",
  ],
};
