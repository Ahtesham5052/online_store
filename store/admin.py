from django.contrib import admin
from django.db.models import Count
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html,urlencode
from django.urls import reverse
from .models import ProductImage 
from . import models
# Register your models here.

class ProductImageInline(admin.TabularInline):
    readonly_fields = ['thumbnail']
    model = ProductImage
    def thumbnail(self,instance):
        if instance.image.name !='':
            return format_html(f'<img src={instance.image.url}/>')
        return ''


class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [ 
            ('<10', 'LOW'),
            ('>10', 'OK')]
    def queryset(self, request, queryset):
        if self.value() == "<10":
            return queryset.filter(inventory__lt=10)
        return queryset.filter(inventory__gt=10)


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']
    @admin.display(ordering='products_count')
    def products_count(self,collection):
        url = (
            reverse('admin:store_product_changelist') 
            + '?' 
            + urlencode({ 
                'collection__id': str(collection.id)
                }))
        return format_html('<a href={}>{}</a>', url, collection.products_count)
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count = Count('product')
        )
    

@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    class Media:
        css ={
            'all': ['styles.css']
        }
    
    
    
    actions = ['clear_inventory']
    autocomplete_fields = ['collection']
    list_display = ['title', 'unit_price', 'inventory_status', 'collection_title']
    list_editable = ['unit_price']
    list_per_page = 10
    list_filter = ['collection', 'last_update', InventoryFilter]
    inlines = [ProductImageInline]
    search_fields = ['title']
    prepopulated_fields = {
        'slug': ['title']
    }
    @admin.display(ordering = 'title')
    def collection_title(self,product):
        return product.collection.title

    @admin.display(ordering='inventory')
    def inventory_status(self,product):
        if product.inventory<10:
            return 'LOW'
        return 'OK'
    
    @admin.action(description='Clear Inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{updated_count} products were successfully updated',
            )

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'membership']
    list_editable = ['membership']
    list_select_related = ['user']
    ordering = ['user__first_name', 'user__last_name']
    search_fields = ['first_name__istartswith','last_name__istartswith']


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['product']
    model = models.OrderItem
    extra = 0
    min_num = 1
    max_num = 10

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    list_display = ['id','placed_at', 'payment_status', 'customer']
    list_editable = ['payment_status']
    inlines = [OrderItemInline]
