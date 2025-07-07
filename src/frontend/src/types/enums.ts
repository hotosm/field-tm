export enum task_split_type {
  DIVIDE_ON_SQUARE = 'DIVIDE_ON_SQUARE',
  CHOOSE_AREA_AS_TASK = 'CHOOSE_AREA_AS_TASK',
  TASK_SPLITTING_ALGORITHM = 'TASK_SPLITTING_ALGORITHM',
}

export enum task_event {
  MAP = 'MAP',
  FINISH = 'FINISH',
  VALIDATE = 'VALIDATE',
  GOOD = 'GOOD',
  BAD = 'BAD',
  SPLIT = 'SPLIT',
  MERGE = 'MERGE',
  ASSIGN = 'ASSIGN',
  COMMENT = 'COMMENT',
}

export enum task_state {
  UNLOCKED_TO_MAP = 'UNLOCKED_TO_MAP',
  LOCKED_FOR_MAPPING = 'LOCKED_FOR_MAPPING',
  UNLOCKED_TO_VALIDATE = 'UNLOCKED_TO_VALIDATE',
  LOCKED_FOR_VALIDATION = 'LOCKED_FOR_VALIDATION',
  UNLOCKED_DONE = 'UNLOCKED_DONE',
}

export enum task_state_labels {
  UNLOCKED_TO_MAP = 'Ready',
  LOCKED_FOR_MAPPING = 'Locked For Mapping',
  UNLOCKED_TO_VALIDATE = 'Ready For Validation',
  LOCKED_FOR_VALIDATION = 'Locked For Validation',
  UNLOCKED_DONE = 'Validated',
}

export enum entity_state {
  READY = 0,
  OPENED_IN_ODK = 1,
  SURVEY_SUBMITTED = 2,
  VALIDATED = 5,
  MARKED_BAD = 6,
}

export enum user_roles {
  READ_ONLY = 'READ_ONLY',
  MAPPER = 'MAPPER',
  ADMIN = 'ADMIN',
}

export enum project_roles {
  MAPPER = 'MAPPER',
  VALIDATOR = 'VALIDATOR',
  FIELD_MANAGER = 'FIELD_MANAGER',
  PROJECT_MANAGER = 'PROJECT_MANAGER',
  ASSOCIATE_PROJECT_MANAGER = 'ASSOCIATE_PROJECT_MANAGER',
}

export type MapGeomTypes = {
  POINT: 'POINT';
  POLYGON: 'POLYGON';
  POLYLINE: 'POLYLINE';
};

export enum GeoGeomTypesEnum {
  POINT = 'POINT',
  POLYGON = 'POLYGON',
  POLYLINE = 'POLYLINE',
}

export enum submission_status {
  null = 'Received',
  hasIssues = 'Has issues',
  edited = 'Edited',
  approved = 'Approved',
  rejected = 'Rejected',
}

export enum osm_forms {
  buildings = 'OSM Buildings',
  health = 'OSM Healthcare',
}

export enum project_visibility {
  PUBLIC = 'PUBLIC',
  PRIVATE = 'PRIVATE',
}

export enum project_status {
  DRAFT = 'DRAFT',
  PUBLISHED = 'PUBLISHED',
  ARCHIVED = 'ARCHIVED',
  COMPLETED = 'COMPLETED',
}

export enum data_extract_type {
  OSM = 'osm_data_extract',
  CUSTOM = 'custom_data_extract',
  NONE = 'no_data_extract',
}
