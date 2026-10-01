from functools import wraps

from django.contrib.auth.decorators import user_passes_test


def has_panel_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, "manager_profile", None)
    return profile is not None and profile.is_active


def admin_required(view_func):
    @wraps(view_func)
    @user_passes_test(has_panel_access, login_url="/login/")
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped