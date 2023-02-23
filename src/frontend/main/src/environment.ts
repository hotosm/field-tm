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
    "READY",
    "LOCKED_FOR_MAPPING",
    "LOCKED_FOR_VALIDATION",
    "VALIDATE",
    "INVALIDATED",
    "BAD",
    "SPLIT",
    "ARCHIVED",
  ],
};
