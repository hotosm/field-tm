export type roleType = 'READ_ONLY' | 'MAPPER' | 'ADMIN';

export type mappingLevelType = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';

export type projectRoleType =
  | 'MAPPER'
  | 'VALIDATOR'
  | 'FIELD_MANAGER'
  | 'ASSOCIATE_PROJECT_MANAGER'
  | 'PROJECT_MANAGER';

export type userType = {
  id: number;
  username: string;
  role: roleType;
  profile_img: string;
  name: string;
  city: string;
  country: string;
  email_address: string;
  is_email_verified: boolean;
  is_expert: boolean;
  mapping_level: mappingLevelType;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_invalidated: number;
  projects_mapped: number[];
  registered_at: string;
  project_roles: Record<string, projectRoleType>;
  orgs_managed: number[];
};
