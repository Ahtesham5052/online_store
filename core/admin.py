from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from tags.models import TagItem
from store.admin import ProductAdmin, ProductImageInline
from store.models import Product
from .models import User

# Register your models here.

class TagInline(GenericTabularInline):
    autocomplete_fields = ['tag']
    model = TagItem
    extra = 1


class CustomProductAdmin(ProductAdmin):
    inlines = [TagInline, ProductImageInline]

admin.site.unregister(Product)
admin.site.register(Product,CustomProductAdmin)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "email", "first_name", "last_name"),
            },
        ),
    )

