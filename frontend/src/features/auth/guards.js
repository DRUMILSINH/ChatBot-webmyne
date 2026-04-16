import { Fragment as _Fragment, jsx as _jsx } from "react/jsx-runtime";
export function RoleGuard({ children }) {
    // UI-level guard placeholder. Backend still enforces RBAC.
    return _jsx(_Fragment, { children: children });
}
