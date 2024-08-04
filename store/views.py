from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,DestroyModelMixin,ListModelMixin,UpdateModelMixin
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.viewsets import ModelViewSet,GenericViewSet
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.decorators import action
from .models import Product,Collection,Order,OrderItem,Review,Cart,CartItem,Customer,ProductImage
from .serializers import ProductSerializer,UpdateOrderSerializer,CollectionSerializer,ProductImageSerializer,ReviewSerializer,CreateOrderSerializer,OrderItemSerializer,CartSerializer,CartItemSerializer,AddCartItemSerializer,UpdateCartItemSerializer,OrderSerializer,CustomerSerializer
from .filters import ProductFilter
from .pagination import DefaultPagination
# Create your views here.


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    ordering_fields = ['unit_price', 'last_update']
    search_fields = ['title', 'description']
     

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count()>0:
            return Response({"error": "Product cannot be deleted because it's associated with order items"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

        
class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']).count()>0:
            return Response({"error": "Cannot delete this collection because we have it's product"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        return Review.objects.filter(product_id = self.kwargs['product_pk'])
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}
     

class CartViewSet(CreateModelMixin,DestroyModelMixin, GenericViewSet, RetrieveModelMixin,ListModelMixin):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer

class CartItemViewSet(ModelViewSet):
    http_method_names = ['get','post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer 

    def get_queryset(self):
        return CartItem.objects.filter(cart_id = self.kwargs['cart_pk']).select_related('product')
    
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}
    

class CustomerViewSet(CreateModelMixin,RetrieveModelMixin,UpdateModelMixin,GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False,methods=['GET','PUT'])
    def me(self,request):
        customer = Customer.objects.get_or_create(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return serializer.data 
        

class OrderViewSet(ModelViewSet):
    http_method_names = ['get','patch','delete','head','options']
    
    def get_permissions(self):
        if self.request.method in ['PUT','PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer_id = Customer.objects.only('id').get_or_create(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer
    
    def get_serializer_context(self):
        return {'user_id': self.request.user.id}
    

class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer
    
    def get_queryset(self):
        return ProductImage.objects.filter(product_id= self.kwargs['product_pk'])
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}