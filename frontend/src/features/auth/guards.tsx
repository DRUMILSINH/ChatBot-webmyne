import { PropsWithChildren } from 'react';

export function RoleGuard({ children }: PropsWithChildren) {
  // UI-level guard placeholder. Backend still enforces RBAC.
  return <>{children}</>;
}
