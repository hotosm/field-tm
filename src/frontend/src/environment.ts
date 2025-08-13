import { basemap_providers, task_event, task_state, tile_output_formats } from '@/types/enums';
import { variantType } from '@/components/common/Button';

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
      action: [{ key: 'Assign To Mapper', value: 'MAP', btnType: 'primary-red' }],
    },
    {
      label: 'LOCKED_FOR_MAPPING',
      action: [
        { key: 'Mark as fully mapped', value: 'FINISH', btnType: 'primary-grey' },
        { key: 'Stop Mapping', value: 'BAD', btnType: 'link-red' },
      ],
    },
    {
      label: 'UNLOCKED_TO_VALIDATE',
      action: [
        { key: 'Start Validation', value: 'VALIDATE', btnType: 'primary-grey' },
        { key: 'Reset', value: 'BAD', btnType: 'secondary-red' },
      ],
    },
    {
      label: 'LOCKED_FOR_VALIDATION',
      action: [
        { key: 'Mark As Validated', value: 'GOOD', btnType: 'primary-grey' },
        { key: 'Mapping Needed', value: 'BAD', btnType: 'link-red' },
      ],
    },
    {
      label: 'UNLOCKED_DONE',
      action: [
        { key: 'Reset', value: 'BAD', btnType: 'primary-grey' },
        // { key: 'Merge data with OSM', value: 'CONFLATE', btnType: 'grey-red' },
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
} as configType;

type configType = {
  tasksStatus: { label: task_state; action: { key: string; value: task_event; btnType: variantType }[] }[];
  baseMapProviders: { id: number; label: string; value: basemap_providers }[];
  tileOutputFormats: { id: number; label: string; value: tile_output_formats }[];
};
