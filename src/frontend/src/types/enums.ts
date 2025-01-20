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

export enum entity_state {
  READY = 0,
  OPENED_IN_ODK = 1,
  SURVEY_SUBMITTED = 2,
  MARKED_BAD = 6,
}

export enum user_roles {
  READ_ONLY = 'READ_ONLY',
  MAPPER = 'MAPPER',
  ADMIN = 'ADMIN',
}

export type NewGeomTypes = {
  POINT: 'POINT';
  POLYGON: 'POLYGON';
  LINESTRING: 'LINESTRING';
};

export enum submission_status {
  null = 'Received',
  hasIssues = 'Has issues',
  edited = 'Edited',
  approved = 'Approved',
  rejected = 'Rejected',
}
