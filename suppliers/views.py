import calendar
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from .decorators import admin_required, has_panel_access
from .forms import StatusForm, SupplierForm
from .models import STATUSES, CalendarNote, Manager, Supplier, get_status_label
from django.contrib.auth.mixins import LoginRequiredMixin

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
          "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

def months_back(day, n):
    total = day.year * 12 + (day.month - 1) - n
    year, m = divmod(total, 12)
    m += 1
    last = calendar.monthrange(year, m)[1]
    return day.replace(year=year, month=m, day=min(day.day, last))

def current_manager(request):
    profile = getattr(request.user, "manager_profile", None)
    if profile is None or not profile.is_active:
        return None
    return profile


def paginate(queryset, request, per_page, param="page"):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(param) or 1
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def scoped_suppliers(request):
    if request.user.is_superuser:
        return Supplier.objects.select_related("responsible_manager")
    profile = current_manager(request)
    if profile is None:
        return Supplier.objects.none()
    return Supplier.objects.filter(responsible_manager=profile).select_related(
        "responsible_manager"
    )

PAGE_SIZE = 20


class SupplierListView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get("q", "").strip()
        status = request.GET.get("status", "").strip()
        manager = request.GET.get("manager", "").strip()
        suppliers = Supplier.objects.select_related("responsible_manager")
        if q:
            suppliers = suppliers.filter(
                Q(full_name__icontains=q)
                | Q(organization__icontains=q)
                | Q(city__icontains=q)
                | Q(region__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
                | Q(responsible_manager__full_name__icontains=q)
            )
        if status in dict(STATUSES):
            suppliers = suppliers.filter(status=status)
        if manager:
            suppliers = suppliers.filter(responsible_manager__full_name=manager)

        managers = (
            Manager.objects.filter(is_active=True)
            .order_by("full_name")
            .values_list("full_name", flat=True)
        )

        page_obj = paginate(
            suppliers.order_by("-last_activity", "-id"),
            request,
            PAGE_SIZE,
            param="page",
        )
        return render(request, "suppliers/list.html", {
            "suppliers": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": page_obj.paginator,
            "statuses": STATUSES,
            "managers": managers,
            "q": q,
            "status": status,
            "selected_manager": manager,
        })

class PanelAccessMixin(UserPassesTestMixin):
    login_url = "/login/"

    def requires_panel_access(self):
        return True

    def test_func(self):
        if not self.requires_panel_access():
            return True
        return has_panel_access(self.request.user)

    def handle_no_permission(self):
        if self.panel:
            return redirect(f"{self.login_url}?next={self.request.path}")
        return super().handle_no_permission()


def supplier_form(request, instance=None, data=None):
    form = SupplierForm(data, instance=instance)
    if not request.user.is_superuser:
        form.fields.pop("responsible_manager", None)
    return form


class SupplierCreateView(PanelAccessMixin, LoginRequiredMixin, View):
    panel = False
    title = "Создать заказчика"

    def get_template_name(self):
        if self.panel:
            return "suppliers/admin_supplier_form.html"
        return "suppliers/form.html"

    def get_success_url(self, supplier):
        if self.panel:
            return reverse("suppliers:admin_edit", args=[supplier.id])
        return reverse("suppliers:detail", args=[supplier.id])

    def get_context(self, form):
        return {"form": form, "supplier": None, "title": self.title}

    def get(self, request):
        return render(
            request,
            self.get_template_name(),
            self.get_context(supplier_form(request)),
        )

    def post(self, request):
        form = supplier_form(request, data=request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            if not request.user.is_superuser:
                supplier.responsible_manager = current_manager(request)
            supplier.save()
            messages.success(request, f"Заказчик '{supplier.full_name}' создан.")
            return redirect(self.get_success_url(supplier))
        return render(request, self.get_template_name(), self.get_context(form))


class SupplierUpdateView(PanelAccessMixin, LoginRequiredMixin, View):
    panel = False
    title = "Редактировать заказчика"

    def requires_panel_access(self):
        return self.panel

    def get_template_name(self):
        if self.panel:
            return "suppliers/admin_supplier_form.html"
        return "suppliers/form.html"

    def get_success_url(self, supplier):
        if self.panel:
            return reverse("suppliers:admin_edit", args=[supplier.id])
        return reverse("suppliers:detail", args=[supplier.id])

    def get_context(self, form, supplier):
        context = {"form": form, "supplier": supplier, "title": self.title}
        if self.panel:
            context["today"] = date.today()
        return context

    def get_object(self, request, pk):
        return get_object_or_404(scoped_suppliers(request), pk=pk)

    def get(self, request, pk):
        supplier = self.get_object(request, pk)
        form = supplier_form(request, instance=supplier)
        return render(request, self.get_template_name(), self.get_context(form, supplier))

    def post(self, request, pk):
        supplier = self.get_object(request, pk)
        form = supplier_form(request, instance=supplier, data=request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            if not request.user.is_superuser:
                supplier.responsible_manager = current_manager(request)
            supplier.save()
            messages.success(request, f"Заказчик '{supplier.full_name}' обновлён.")
            return redirect(self.get_success_url(supplier))
        return render(request, self.get_template_name(), self.get_context(form, supplier))

class SupplierDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
        return render(request, "suppliers/detail.html", {"supplier": supplier})

class SupplierStatusView(LoginRequiredMixin, View):
    def get(self, request, pk):
        supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
        form = StatusForm(initial={"status": supplier.status})
        return render(request, "suppliers/status.html", {"form": form, "supplier": supplier})
    
    def post(self, request, pk):
        supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
        form = StatusForm(request.POST)
        if form.is_valid():
            supplier.status = form.cleaned_data["status"]
            supplier.save()
            messages.success(
                request,
                f"Статус заказчика '{supplier.full_name}' изменён на '{supplier.status_display}'.",
            )
            return redirect(reverse("suppliers:detail", args=[supplier.id]))
        return render(request, "suppliers/status.html", {"form": form, "supplier": supplier})

class SupplierDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
        supplier.is_active = False
        supplier.save()
        messages.success(request, f"Заказчик '{supplier.full_name}' деактивирован.")
        return redirect(reverse("suppliers:detail", args=[supplier.id]))

@admin_required
def dashboard(request):
    suppliers = scoped_suppliers(request)
    totals = suppliers.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        cities_count=Count("city", distinct=True, filter=~Q(city="")),
        managers_count=Count("responsible_manager", distinct=True),
    )
    counted = {
        row["status"]: row["cnt"]
        for row in suppliers.order_by().values("status").annotate(cnt=Count("id"))
    }
    status_rows = [
    (value, label, counted.get(value, 0)) for value, label in STATUSES
]
    total = totals["total"]
    context = {
        "total": total,
        "active": totals["active"],
        "inactive": total - totals["active"],
        "cities_count": totals["cities_count"],
        "managers_count": totals["managers_count"],
        "status_rows": status_rows,
        "recent_suppliers": suppliers.order_by("-last_activity")[:5],
        "status_choices": STATUSES,
    }
    return render(request, "suppliers/admin_dashboard.html", context)

def parse_calendar_period(request, today):
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if not (1900 <= year <= 2100 and 1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month
    return year, month


def parse_calendar_date(raw, fallback):
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        return fallback


def scoped_calendar_notes(user):
    if user.is_superuser:
        return CalendarNote.objects.all()
    return CalendarNote.objects.filter(author=user)


def calendar_redirect(year, month, day):
    return redirect(
        f"{reverse('suppliers:admin_calendar')}"
        f"?year={year}&month={month}&date={day.isoformat()}"
    )


def handle_calendar_note(request, year, month, today):
    if "add_note" in request.POST:
        note_date = parse_calendar_date(request.POST.get("date", ""), today)
        text = request.POST.get("text", "").strip()
        if text:
            CalendarNote.objects.create(date=note_date, text=text, author=request.user)
        return calendar_redirect(year, month, note_date)
    if "delete_note" in request.POST:
        note = get_object_or_404(CalendarNote, pk=request.POST.get("note_id"))
        note_date = note.date
        if request.user.is_superuser or note.author == request.user:
            note.delete()
        return calendar_redirect(year, month, note_date)
    return None


def calendar_note_counts(notes_qs, year, month):
    return dict(
        notes_qs.filter(date__year=year, date__month=month)
        .values("date")
        .annotate(cnt=Count("id"))
    )


def calendar_activity_counts(scope, year, month, cutoff):
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
    return day_counts, overdue_counts


def build_calendar_grid(year, month, day_counts, overdue_counts, notes_per_day):
    days_in_month = calendar.monthrange(year, month)[1]
    cells = [None] * date(year, month, 1).weekday()
    for day in range(1, days_in_month + 1):
        cells.append({
            "day": day,
            "iso": f"{year}-{month:02d}-{day:02d}",
            "total": day_counts.get(day, 0),
            "overdue": overdue_counts.get(day, 0),
            "notes": notes_per_day.get(date(year, month, day), 0),
        })
    while len(cells) % 7:
        cells.append(None)
    return cells


def month_neighbors(year, month):
    days_in_month = calendar.monthrange(year, month)[1]
    prev = date(year, month, 1) - timedelta(days=1)
    nxt = date(year, month, days_in_month) + timedelta(days=1)
    return prev, nxt


@admin_required
def admin_calendar(request):
    today = date.today()
    year, month = parse_calendar_period(request, today)

    if request.method == "POST":
        response = handle_calendar_note(request, year, month, today)
        if response is not None:
            return response

    scope = scoped_suppliers(request)
    notes_qs = scoped_calendar_notes(request.user)
    cutoff = months_back(today, 3)

    notes_per_day = calendar_note_counts(notes_qs, year, month)
    selected = parse_calendar_date(request.GET.get("date", ""), today)
    day_counts, overdue_counts = calendar_activity_counts(scope, year, month, cutoff)
    cells = build_calendar_grid(year, month, day_counts, overdue_counts, notes_per_day)
    prev, nxt = month_neighbors(year, month)

    context = {
        "year": year,
        "month": month,
        "month_name": MONTHS[month - 1],
        "weekdays": WEEKDAYS,
        "cells": cells,
        "today": today,
        "cutoff": cutoff,
        "overdue": scope.filter(last_activity__lt=cutoff).order_by("last_activity"),
        "selected": selected,
        "selected_notes": notes_qs.filter(date=selected).order_by("-created_at"),
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

    if selected and not selected.isdigit():
        return redirect("suppliers:admin_managers")

    managers = (
        scope.filter(responsible_manager__isnull=False)
        .values("responsible_manager_id", "responsible_manager__full_name")
        .annotate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )
        .order_by("-total")
    )
    manager_data = []
    for m in managers:
        manager_data.append({
            "id": m["responsible_manager_id"],
            "name": m["responsible_manager__full_name"],
            "total": m["total"],
            "active": m["active"],
            "inactive": m["total"] - m["active"],
        })

    suppliers = None
    selected_name = ""
    if selected:
        suppliers = scope.filter(responsible_manager_id=selected).order_by("-last_activity")
        selected_name = (
            Manager.objects.filter(pk=selected).values_list("full_name", flat=True).first() or ""
        )

    context = {
        "managers": manager_data,
        "selected": selected,
        "selected_name": selected_name,
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


@admin_required
def admin_supplier_activity(request, pk):
    supplier = get_object_or_404(scoped_suppliers(request), pk=pk)
    if request.method == "POST":
        if request.POST.get("mark_today"):
            when = date.today()
        else:
            raw = request.POST.get("last_activity", "").strip()
            try:
                when = date.fromisoformat(raw)
            except ValueError:
                messages.error(request, "Некорректная дата.")
                return redirect(reverse("suppliers:admin_edit", args=[supplier.id]))
            if when > date.today():
                messages.error(request, "Дата активности не может быть в будущем.")
                return redirect(reverse("suppliers:admin_edit", args=[supplier.id]))
        supplier.mark_active(when)
        if when == date.today():
            messages.success(request, f"Активность '{supplier.full_name}' отмечена сегодня.")
        else:
            messages.success(
                request, f"Активность '{supplier.full_name}': {when.strftime('%d.%m.%Y')}."
            )
    return redirect(reverse("suppliers:admin_edit", args=[supplier.id]))
