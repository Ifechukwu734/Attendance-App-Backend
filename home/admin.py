from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
# Register your models here.


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("email", "is_staff", "is_active", )
    list_filter = ("email", "is_staff", "is_active", )
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name",  "department", "level",)}),
        ("permissions", {"fields": ("is_staff", "is_active","groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "first_name", "last_name",  "department", "level", "is_staff", "is_active", 
            )
        }),
    )

    search_fields = ("email", )
    ordering = ("email",)


admin.site.register(CustomUser, CustomUserAdmin)