from django import forms

from .models import STATUSES, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "full_name",
            "region",
            "city",
            "organization",
            "phone",
            "email",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "organization": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Новый статус",
        choices=STATUSES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
