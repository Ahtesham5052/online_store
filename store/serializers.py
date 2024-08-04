from rest_framework import serializers
from .models import Product,Collection,Review,Cart,CartItem,Customer,Order,OrderItem,ProductImage
from .signals import order_created
from decimal import Decimal
from django.db import transaction

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'product_count']

    product_count = serializers.SerializerMethodField(method_name='product_counter')    
    
    def product_counter(self,collection:Collection):
        return collection.product.count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id,**validated_data)
    
    
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'unit_price', 'slug', 'inventory', 'price_with_tax', 'collection','images']
    
    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    
    def calculate_tax(self, product:Product):
        return product.unit_price * Decimal(1.1) 
    

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date', 'name', 'description']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id = product_id, **validated_data) 


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    class Meta:
        model = CartItem
        fields = ['id','product_id','quantity']

    def validated_product_id(self,value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Product doesnot exists with id')
        return value
    
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id,product_id=product_id,quantity=quantity)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id,**self.validated_data)
            return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    def get_total_price(self,cartitem:CartItem):
        return cartitem.product.unit_price * cartitem.quantity


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    
    def get_total_price(self,cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])
    
    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'items', 'total_price']


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()    

    class Meta: 
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_day', 'membership']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer
    class Meta:
        model = OrderItem
        fields = ['id','product','unit_price','quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer
    class Meta:
        model = Order
        fields = ['id', 'customer', 'placed_at', 'payment_status', 'items']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    def save(self, **kwargs):
        with transaction.atomic():        
            cart_id = self.validated_data['cart_id']
            (customer , created) = Customer.objects.get_or_create(user_id = self.context['user_id'])
            order= Order.objects.create(customer=customer) 
            cart_items = CartItem.objects.select_related('products').filter(cart_id=cart_id)
            order_items = [
                OrderItem(
                order = order,
                product = item.product,
                unit_price = item.product.unit_price,
                quantity = item.quantity

                )for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(pk = cart_id).delete()
            order_created.send_robust(self.__class__,order=order)
            return order
    
    def validate_cart_id(self,cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart Exists')
        elif CartItem.objects.filter(cart_id=cart_id).count()==0:
            raise serializers.ValidationError('No items in cart')
        return cart_id
    

class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']

