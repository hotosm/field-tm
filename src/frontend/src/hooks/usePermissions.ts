import { project_roles } from '@/types/enums';
import CoreModules from '@/shared/CoreModules';

export function useIsAdmin() {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  return !!authDetails?.is_admin;
}

export function useIsProjectManager(id: string | number | null) {
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  return !!authDetails?.is_admin || authDetails?.project_roles?.[id] === project_roles.PROJECT_ADMIN;
}
