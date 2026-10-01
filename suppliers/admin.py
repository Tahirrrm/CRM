from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from .models import Manager, Supplier

SUPPLIER_PERM_CODENAMES = ["view_supplier", "change_supplier"]
MANAGER_GROUP = "Менеджеры"
SUPERUSER_GROUP = "Суперпользователи CRM"


def active_manager(request):
    if request.user.is_superuser:
        return None
    profile = getattr(request.user, "manager_profile", None)
    if profile is None or not profile.is_active:
        return None
    return profile


class ManagerInline(admin.StackedInline):
    model = Manager
    verbose_name = "Профиль менеджера"
    verbose_name_plural = "Профили менеджеров"
    can_delete = False
    extra = 0

    def has_view_permission(self, request, obj=None):
        profile = active_manager(request)
        return obj is None or profile is not None

    def has_change_permission(self, request, obj=None):
        return active_manager(request) is not None

    def has_add_permission(self, request, obj=None):
        return active_manager(request) is not None

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class UserWithManagerAdmin(UserAdmin):
    inlines = [ManagerInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        profile = active_manager(request)
        if profile is None:
            return qs.none()
        return qs.filter(pk=profile.user_id)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        profile = active_manager(request)
        return profile is not None and obj.pk == profile.user_id

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        ro = ["is_superuser", "is_staff", "user_permissions", "groups"]
        if not request.user.is_superuser:
            ro += [
                "password",
                "last_login",
                "date_joined",
                "is_active",
                "is_superuser",
                "is_staff",
                "user_permissions",
                "groups",
            ]
        return tuple(dict.fromkeys(ro))


admin.site.unregister(User)
admin.site.register(User, UserWithManagerAdmin)


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "user_is_active", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "user__username")
    autocomplete_fields = ("user",)

    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description="Пользователь активен", boolean=True)
    def user_is_active(self, obj):
        return obj.user.is_active


admin.site.unregister(Group)
admin.site.register(Group)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "organization", "city", "phone", "status", "responsible_manager", "is_active", "last_activity")
    list_filter = ("status", "is_active", "city")
    search_fields = ("full_name", "organization", "phone", "email")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("responsible_manager")
        if request.user.is_superuser:
            return qs
        profile = active_manager(request)
        if profile is None:
            return qs.none()
        return qs.filter(responsible_manager=profile)

    def has_module_perms(self, request):
        return request.user.is_superuser or active_manager(request) is not None

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profile = active_manager(request)
        if profile is None:
            return False
        if obj is None:
            return True
        return obj.responsible_manager_id == profile.id

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return ("responsible_manager", "created_at", "last_activity")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profile = active_manager(request)
        if profile is None:
            return False
        if obj is not None:
            return obj.responsible_manager_id == profile.id
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.responsible_manager = active_manager(request)
        super().save_model(request, obj, form, change)