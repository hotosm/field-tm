import { project_roles } from '@/types/enums';

export type mappingLevelType = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';

export type projectRoleType = 'MAPPER' | 'PROJECT_ADMIN';

export type userType = {
  sub: string;
  username: string;
  // Global admin flag from backend; replaces legacy global role enum
  is_admin: boolean;
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

export type projectUserInvites = {
  token: string;
  project_id: number;
  osm_username: string | null;
  email: string | null;
  role: project_roles;
  expires_at: string;
  used_at: string | null;
  created_at: string;
};
