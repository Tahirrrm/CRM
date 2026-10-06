from django import forms

from .models import STATUSES, Manager, Supplier


class SupplierForm(forms.ModelForm):
    responsible_manager = forms.ModelChoiceField(
        queryset=Manager.objects.filter(is_active=True),
        required=False,
        label="Ответственный менеджер",
        empty_label="— не назначен —",
    )

    class Meta:
        model = Supplier
        fields = [
            "full_name",
            "region",
            "city",
            "organization",
            "phone",
            "email",
            "status",
            "is_active",
            "responsible_manager",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "organization": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Новый статус",
        choices=STATUSES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )