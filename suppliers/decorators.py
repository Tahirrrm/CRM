from functools import wraps

from django.contrib.auth.decorators import user_passes_test


def admin_required(view_func):
    @wraps(view_func)
    @user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or u.is_staff),
        login_url="/admin/login/",
    )
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped