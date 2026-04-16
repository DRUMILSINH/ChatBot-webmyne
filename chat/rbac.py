from functools import wraps

from django.conf import settings
from django.http import JsonResponse


def user_has_role(user, roles: tuple[str, ...]) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def role_required(*roles: str, force: bool = False):
    """
    Enforces role-based access when ENFORCE_RBAC=True.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            enforce_rbac = force or getattr(settings, "ENFORCE_RBAC", False)
            if not enforce_rbac:
                return view_func(request, *args, **kwargs)

            if not getattr(request.user, "is_authenticated", False):
                return JsonResponse({"error": "Authentication required."}, status=401)

            if not user_has_role(request.user, roles):
                return JsonResponse({"error": "Insufficient permissions."}, status=403)

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
