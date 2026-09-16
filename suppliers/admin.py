from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Manager, Supplier

class ManagerInline(admin.StackedInline):
    model = Manager
    verbose_name = "Профиль менеджера"
    verbose_name_plural = "Профиль менеджера"
    can_delete = False
    extra = 0

class UserWithManagerAdmin(UserAdmin):
    inlines = [ManagerInline]

admin.site.unregister(User)
admin.site.register(User, UserWithManagerAdmin)

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "user_is_active", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "user__username")
    autocomplete_fields = ("user",)

    @admin.display(description="Аккаунт активен", boolean=True)
    def user_is_active(self, obj):
        return obj.user.is_active

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "organization", "city", "phone", "status", "responsible_manager", "is_active", "last_activity")
    list_filter = ("status", "is_active", "city")
    search_fields = ("full_name", "organization", "phone", "email")
    list_editable = ("status", "is_active")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, "manager_profile"):
            return qs.filter(responsible_manager=request.user.manager_profile.full_name)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return ("responsible_manager",)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is not None:
            if not hasattr(request.user, "manager_profile"):
                return False
            return obj.responsible_manager == request.user.manager_profile.full_name
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and hasattr(request.user, "manager_profile"):
            obj.responsible_manager = request.user.manager_profile.full_name
        super().save_model(request, obj, form, change)