import { project_roles } from '@/types/enums';
import CoreModules from '@/shared/CoreModules';

export function useIsAdmin() {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  return !!authDetails?.is_admin;
}

export function useHasManagedAnyOrganization() {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const orgs_managed = authDetails?.orgs_managed || [];
  return !!authDetails?.is_admin || orgs_managed?.length > 0;
}

export function useIsOrganizationAdmin(id: number | null) {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  return !!authDetails?.is_admin || (authDetails?.orgs_managed && authDetails?.orgs_managed?.includes(id));
}

export function useIsProjectManager(id: string | number | null) {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  return !!authDetails?.is_admin || authDetails?.project_roles?.[id] === project_roles.PROJECT_ADMIN;
}
