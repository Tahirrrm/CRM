from django.urls import path

from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.SupplierListView.as_view(), name="list"),
    path("create/", views.SupplierCreateView.as_view(), name="create"),
    path("<int:pk>/", views.SupplierDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="edit"),
    path("<int:pk>/status/", views.SupplierStatusView.as_view(), name="status"),
    path("<int:pk>/deactivate/", views.SupplierDeactivateView.as_view(), name="deactivate"),
    path("admin-panel/", views.dashboard, name="admin_dashboard"),
    path("admin-panel/calendar/", views.admin_calendar, name="admin_calendar"),
    path("admin-panel/managers/", views.admin_managers, name="admin_managers"),
    path("admin-panel/suppliers/", views.admin_supplier_list, name="admin_list"),
    path("admin-panel/suppliers/new/", views.admin_supplier_create, name="admin_create"),
    path("admin-panel/suppliers/<int:pk>/edit/", views.admin_supplier_edit, name="admin_edit"),
    path("admin-panel/suppliers/<int:pk>/delete/", views.admin_supplier_delete, name="admin_delete"),
    path("admin-panel/suppliers/<int:pk>/toggle/", views.admin_supplier_toggle, name="admin_toggle"),
    path("admin-panel/suppliers/<int:pk>/activity/", views.admin_supplier_activity, name="admin_activity"),
]
