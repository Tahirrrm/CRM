import calendar
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from .decorators import admin_required
from .forms import StatusForm, SupplierForm
from .models import STATUSES, CalendarNote, Manager, Supplier

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
          "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

def months_back(day, n):
    total = day.year * 12 + (day.month - 1) - n
    year, m = divmod(total, 12)
    m += 1
    last = calendar.monthrange(year, m)[1]
    return day.replace(year=year, month=m, day=min(day.day, last))

def scoped_suppliers(request):
    if request.user.is_superuser:
        return Supplier.objects.all()
    if hasattr(request.user, "manager_profile"):
        profile = request.user.manager_profile
        if not profile.is_active:
            return Supplier.objects.none()
        return Supplier.objects.filter(responsible_manager=profile.full_name)
    return Supplier.objects.none()

def scoped_managers(request):
    if request.user.is_superuser:
        return Supplier.objects.exclude(responsible_manager__isnull=True).exclude(responsible_manager="")
    if hasattr(request.user, "manager_profile"):
        name = request.user.manager_profile.full_name
        return Supplier.objects.filter(responsible_manager=name)
    return Supplier.objects.none()

class SupplierListView(View):
    def get(self, request):
        q = request.GET.get("q", "").strip()
        status = request.GET.get("status", "").strip()
        manager = request.GET.get("manager", "").strip()
        suppliers = Supplier.objects.all()
        if q:
            suppliers = suppliers.filter(
                Q(full_name__icontains=q)
                | Q(organization__icontains=q)
                | Q(city__icontains=q)
                | Q(region__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
                | Q(responsible_manager__icontains=q)
            )
        if status in dict(STATUSES):
            suppliers = suppliers.filter(status=status)
        if manager:
            suppliers = suppliers.filter(responsible_manager=manager)

        managers = (
            Supplier.objects.exclude(responsible_manager__isnull=True)
            .exclude(responsible_manager="")
            .values_list("responsible_manager", flat=True)
            .distinct()
            .order_by("responsible_manager")
        )

        return render(request, "suppliers/list.html", {
            "suppliers": suppliers.order_by("-last_activity"),
            "statuses": STATUSES,
            "managers": managers,
            "q": q,
            "status": status,
            "selected_manager": manager,
        })

class SupplierCreateView(UserPassesTestMixin, View):
    login_url = "/admin/login/"

    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        form = SupplierForm()
        return render(request, "suppliers/form.html", {"form": form, "title": "Создать заказчика"})
    
    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            if hasattr(request.user, "manager_profile"):
                supplier.responsible_manager = request.user.manager_profile.full_name
            supplier.save()
            messages.success(request, f"Заказчик '{supplier.full_name}' создан.")
            return redirect(reverse("suppliers:detail", args=[supplier.id]))
        return render(request, "suppliers/form.html", {"form": form, "title": "Создать заказчика"})

class SupplierDetailView(View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        return render(request, "suppliers/detail.html", {"supplier": supplier})

class SupplierUpdateView(View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(instance=supplier)
        return render(request, "suppliers/form.html", {"form": form, "title": "Редактировать заказчика", "supplier": supplier})
    
    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save(commit=False)
            if hasattr(request.user, "manager_profile"):
                supplier.responsible_manager = request.user.manager_profile.full_name
            supplier.save()
            messages.success(request, f"Заказчик '{supplier.full_name}' обновлён.")
            return redirect(reverse("suppliers:detail", args=[supplier.id]))
        return render(request, "suppliers/form.html", {"form": form, "title": "Редактировать заказчика", "supplier": supplier})

class SupplierStatusView(View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = StatusForm(initial={"status": supplier.status})
        return render(request, "suppliers/status.html", {"form": form, "supplier": supplier})
    
    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = StatusForm(request.POST)
        if form.is_valid():
            supplier.status = form.cleaned_data["status"]
            supplier.save()
            messages.success(request, f"Статус заказчика '{supplier.full_name}' изменён на '{supplier.status}'.")
            return redirect(reverse("suppliers:detail", args=[supplier.id]))
        return render(request, "suppliers/status.html", {"form": form, "supplier": supplier})

class SupplierDeactivateView(View):
    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.is_active = False
        supplier.save()
        messages.success(request, f"Заказчик '{supplier.full_name}' деактивирован.")
        return redirect(reverse("suppliers:detail", args=[supplier.id]))

@admin_required
def dashboard(request):
    suppliers = scoped_suppliers(request)
    status_counts = {
        status: suppliers.filter(status=status).count()
        for status, _ in STATUSES
    }
    context = {
        "total": suppliers.count(),
        "active": suppliers.filter(is_active=True).count(),
        "inactive": suppliers.filter(is_active=False).count(),
        "cities_count": suppliers.exclude(city__isnull=True).exclude(city="").values("city").distinct().count(),
        "managers_count": suppliers.exclude(responsible_manager__isnull=True).exclude(responsible_manager="").values("responsible_manager").distinct().count(),
        "status_counts": status_counts,
        "recent_suppliers": suppliers.order_by("-last_activity")[:5],
        "status_choices": STATUSES,
    }
    return render(request, "suppliers/admin_dashboard.html", context)

@admin_required
def admin_calendar(request):
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if not (1900 <= year <= 2100 and 1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month

    scope = scoped_suppliers(request)
    cutoff = months_back(today, 3)

    if request.method == "POST":
        if request.user.is_superuser:
            notes_qs = CalendarNote.objects.all()
        else:
            notes_qs = CalendarNote.objects.filter(author=request.user)
        if "add_note" in request.POST:
            try:
                note_date = date.fromisoformat(request.POST.get("date", ""))
            except ValueError:
                note_date = today
            text = request.POST.get("text", "").strip()
            if text:
                CalendarNote.objects.create(date=note_date, text=text, author=request.user)
            return redirect(
                f"{reverse('suppliers:admin_calendar')}?year={year}&month={month}&date={note_date.isoformat()}"
            )
        if "delete_note" in request.POST:
            note = get_object_or_404(CalendarNote, pk=request.POST.get("note_id"))
            if request.user.is_superuser or note.author == request.user:
                note.delete()
            return redirect(
                f"{reverse('suppliers:admin_calendar')}?year={year}&month={month}&date={note.date.isoformat()}"
            )

    if request.user.is_superuser:
        notes_qs = CalendarNote.objects.all()
    else:
        notes_qs = CalendarNote.objects.filter(author=request.user)

    notes_per_day = dict(
        notes_qs.filter(date__year=year, date__month=month)
        .values("date")
        .annotate(cnt=Count("id"))
    )

    try:
        selected = date.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        selected = today

    selected_notes = notes_qs.filter(date=selected).order_by("-created_at")

    first = date(year, month, 1)
    days_in_month = calendar.monthrange(year, month)[1]
    first_weekday = first.weekday()

    activity = (
        scope.filter(last_activity__year=year, last_activity__month=month)
        .values("last_activity")
        .annotate(cnt=Count("id"))
    )
    day_counts = {r["last_activity"].day: r["cnt"] for r in activity}
    overdue_counts = {
        r["last_activity"].day: r["cnt"]
        for r in activity
        if r["last_activity"] < cutoff
    }

    overdue = scope.filter(last_activity__lt=cutoff).order_by("last_activity")

    prev = first - timedelta(days=1)
    nxt = date(year, month, days_in_month) + timedelta(days=1)

    cells = [None] * first_weekday
    for d in range(1, days_in_month + 1):
        cells.append({
            "day": d,
            "iso": f"{year}-{month:02d}-{d:02d}",
            "total": day_counts.get(d, 0),
            "overdue": overdue_counts.get(d, 0),
            "notes": notes_per_day.get(date(year, month, d), 0),
        })
    while len(cells) % 7:
        cells.append(None)

    context = {
        "year": year,
        "month": month,
        "month_name": MONTHS[month - 1],
        "weekdays": [
            "Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс",
        ],
        "cells": cells,
        "today": today,
        "cutoff": cutoff,
        "overdue": overdue,
        "selected": selected,
        "selected_notes": selected_notes,
        "prev_year": prev.year,
        "prev_month": prev.month,
        "next_year": nxt.year,
        "next_month": nxt.month,
        "is_admin": request.user.is_superuser,
    }
    return render(request, "suppliers/admin_calendar.html", context)


@admin_required
def admin_managers(request):
    selected = request.GET.get("m", "").strip()
    scope = scoped_suppliers(request)

    managers = (
        scope.exclude(responsible_manager__isnull=True)
        .exclude(responsible_manager="")
        .values("responsible_manager")
        .annotate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )
        .order_by("-total")
    )
    manager_data = []
    for m in managers:
        manager_data.append({
            "name": m["responsible_manager"],
            "total": m["total"],
            "active": m["active"],
            "inactive": m["total"] - m["active"],
        })

    suppliers = None
    if selected:
        suppliers = scope.filter(responsible_manager=selected).order_by("-last_activity")

    context = {
        "managers": manager_data,
        "selected": selected,
        "suppliers": suppliers,
        "status_choices": STATUSES,
        "is_admin": request.user.is_superuser,
    }
    return render(request, "suppliers/admin_managers.html", context)


@admin_required
def admin_supplier_list(request):
    suppliers = scoped_suppliers(request).order_by("-last_activity")
    context = {
        "suppliers": suppliers,
        "status_choices": STATUSES,
        "is_admin": request.user.is_superuser,
    }
    return render(request, "suppliers/admin_supplier_list.html", context)


@admin_required
def admin_supplier_create(request):
    managers = list(Manager.objects.filter(is_active=True).values_list("full_name", flat=True))
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        supplier = form.save(commit=False)
        if request.user.is_superuser:
            chosen = request.POST.get("responsible_manager", "").strip()
            if chosen in managers:
                supplier.responsible_manager = chosen
        elif hasattr(request.user, "manager_profile"):
            supplier.responsible_manager = request.user.manager_profile.full_name
        supplier.save()
        messages.success(request, f"Заказчик '{supplier.full_name}' создан.")
        return redirect(reverse("suppliers:admin_edit", args=[supplier.id]))
    context = {
        "form": form,
        "title": "Новый заказчик",
        "status_choices": STATUSES,
        "is_admin": request.user.is_superuser,
        "managers": managers,
    }
    return render(request, "suppliers/admin_supplier_form.html", context)

@admin_required
def admin_supplier_edit(request, pk):
    supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        supplier = form.save(commit=False)
        new_status = request.POST.get("status")
        if new_status in dict(STATUSES):
            supplier.status = new_status
        supplier.is_active = request.POST.get("is_active") == "on"
        if not request.user.is_superuser and hasattr(request.user, "manager_profile"):
            supplier.responsible_manager = request.user.manager_profile.full_name
        supplier.save()
        messages.success(request, f"Заказчик '{supplier.full_name}' обновлён.")
        return redirect(reverse("suppliers:admin_edit", args=[supplier.id]))
    context = {
        "form": form,
        "supplier": supplier,
        "title": "Редактировать заказчика",
        "status_choices": STATUSES,
        "is_admin": request.user.is_superuser,
    }
    return render(request, "suppliers/admin_supplier_form.html", context)

@admin_required
def admin_supplier_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "У вас нет прав на удаление заказчиков.")
        return redirect(reverse("suppliers:admin_list"))
    supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
    if request.method == "POST":
        name = supplier.full_name
        supplier.delete()
        messages.success(request, f"Заказчик '{name}' удалён.")
        return redirect(reverse("suppliers:admin_list"))
    context = {"object": supplier, "type": "заказчика", "name": supplier.full_name}
    return render(request, "suppliers/admin_confirm_delete.html", context)

@admin_required
def admin_supplier_toggle(request, pk):
    supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
    if request.method == "POST":
        supplier.is_active = not supplier.is_active
        supplier.save()
        state = "активирован" if supplier.is_active else "деактивирован"
        messages.success(request, f"Заказчик '{supplier.full_name}' {state}.")
    return redirect(reverse("suppliers:admin_list"))
