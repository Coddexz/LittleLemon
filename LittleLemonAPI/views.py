from rest_framework import generics, permissions, exceptions, status, viewsets, authentication, pagination, filters
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OrderFilter
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CategoryView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    queryset=Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user.is_staff:
            return [permissions.AllowAny()]
        else:
            return [permissions.DjangoModelPermissionsOrAnonReadOnly()]
    
class MenuItems(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    queryset=MenuItem.objects.all()
    serializer_class=MenuItemSerializer
    
    # Add filters
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = '__all__'
    filterset_fields = '__all__'
    
    def get_permissions(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return [permissions.AllowAny()]
        else:
            return [permissions.DjangoModelPermissionsOrAnonReadOnly()]
        

class MenuItemsDetail(generics.RetrieveUpdateDestroyAPIView):
    lookup_field='pk'
    queryset=MenuItem.objects.all()
    serializer_class=MenuItemSerializer
    
    def get_permissions(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return [permissions.AllowAny()]
        else:
            return [permissions.DjangoModelPermissionsOrAnonReadOnly()]
        
class GroupManagement(viewsets.ViewSet):
    
    # Check if manager or super user
    def get_permissions(self):
        user = self.request.user
        if user.is_authenticated:
            if user.groups.filter(name='Manager').exists() or user.is_staff:
                return [permissions.AllowAny()]
            else:
                raise exceptions.PermissionDenied
        else:
            raise exceptions.AuthenticationFailed

    # Get the list of all user of the group
    def list(self, request, group):
        group_name = group.replace('-', ' ').title()
        users = User.objects.all().filter(groups__name=group_name)
        items = UserSerializer(users, many=True)
        return Response(items.data)

    # Add a user to the group
    def create(self, request, group):
        group_name = group.replace('-', ' ').title()
        user = get_object_or_404(User, username=request.data['username'])
        # Check if credentials are valid
        if not authenticate(username=request.data['username'], password=request.data['password']):
            return Response({'message': 'Credentials do not match'}, status=status.HTTP_400_BAD_REQUEST)
        users = Group.objects.get(name=group_name)
        users.user_set.add(user)
        return Response({"message": f"user added to the {group_name} group"}, status=status.HTTP_201_CREATED)
    
class GroupManagementDelete(viewsets.ViewSet):
    # Check if manager or super user
    def get_permissions(self):
        user = self.request.user
        if user.is_authenticated:
            if user.groups.filter(name='Manager').exists() or user.is_staff:
                return [permissions.AllowAny()]
            else:
                raise exceptions.PermissionDenied
        else:
            raise exceptions.AuthenticationFailed
        
    # Delete from the group
    def destroy(self, request, group, id):
        group_name = group.replace('-', ' ').title()
        user = get_object_or_404(User, id=id)
        group = Group.objects.get(name=group_name)
        group.user_set.remove(user)
        message = f'{user.username} deleted from the {group_name} group'
        return Response({'message': message}, status=status.HTTP_200_OK)

# Allow only token authenticated users
@api_view(['GET', 'POST', 'DELETE'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart_items(request):
    # Return current items for the current user
    if request.method == 'GET':
        cart = Cart.objects.all().filter(user_id=request.user.id)
        if not cart:
            return Response({'message': 'You do not have any item in the cart'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Add the menu item to the cart of the current user
    elif request.method == 'POST':
        # If bad request
        try:
            menu_item_id = request.data['food_id']
            menu_item_quantity = request.data['food_quantity']
        except KeyError:
            return Response({'message': 'food_id or food_quantity was not provided'},
                            status=status.HTTP_400_BAD_REQUEST)
        # If quantity negative or not an integer
        menu_item_quantity = float(menu_item_quantity)
        if menu_item_quantity < 0 or not menu_item_quantity.is_integer():
            return Response({'message': 'quantity is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        menu_item_quantity = int(menu_item_quantity)
        
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        price = menu_item_quantity * menu_item.price
        cart_item = Cart(
            user=request.user,
            menuitem=menu_item,
            quantity=menu_item_quantity,
            unit_price=menu_item.price,
            price=price
            )
        cart_item.save()
        message = f'{menu_item_quantity} {menu_item.title} has been added to the cart'
        return Response({'message': message}, status=status.HTTP_201_CREATED)
        
                
    # Delete all menu items created by the current user
    elif request.method == 'DELETE':
        # Get all the cart items of the current user
        cart_items = Cart.objects.filter(user=request.user)
        
        # Delete all items
        cart_items.delete()
        
        return Response({'message': 'All items has been deleted'}, status=status.HTTP_200_OK)
    
    
# Allow only token authenticated users
@api_view(['GET', 'POST'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order(request):
    
    # Check roles of the user
    try:
        user_roles = request.user.groups.all()
    except AttributeError:
        return Response({'message': 'User without a role'}, status=status.HTTP_401_UNAUTHORIZED)

    # Get all groups
    manager_group = Group.objects.get(name='Manager')
    delivery_crew_group = Group.objects.get(name='Delivery Crew')
    customer_group = Group.objects.get(name='Customer')
    
    # Get method
    if request.method == 'GET' and (manager_group in user_roles
                                    or delivery_crew_group in user_roles
                                    or customer_group in user_roles):
            
        # Set pagination
        paginator = pagination.PageNumberPagination()
        
        # Set ordering
        ordering = request.query_params.get('ordering')
        
        # Qualify user to the right role
        #  Return all orders with order items created by all users (paginated)
        if manager_group in user_roles:
            orders = Order.objects.all()
            if not orders:
                return Response({'message': 'There are no orders'}, status=status.HTTP_404_NOT_FOUND)
            
            # If ordering -> order by
            if ordering:
                orders = orders.order_by(ordering)
                
            # Apply filters if any
            if request.query_params:
                orders = OrderFilter().check_filters(orders, request.query_params)
            
            # Return orders
            page = paginator.paginate_queryset(orders, request)
            serializer = OrderSerializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            return paginated_response
        
        # Return all orders with orders assigned to the delivery crew (paginated)
        elif delivery_crew_group in user_roles:
            
            # Get the orders
            try:
                orders = Order.objects.all().filter(delivery_crew_id=request.user.id)
            except AttributeError as e:
                return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)
            if not orders:
                # In case no orders assigned            
                message = {'message': f'No orders found assigned to {request.user.username}'}
                return Response(message, status=status.HTTP_404_NOT_FOUND)
            
            # If ordering -> order by
            if ordering:
                orders = orders.order_by(ordering)
                
            # Return the orders
            page = paginator.paginate_queryset(orders, request)
            serializer = OrderSerializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            return paginated_response
        
        # Returns all orders with order items created by this user (paginated)
        elif customer_group in user_roles:
            orders = Order.objects.all().filter(user=request.user)
            if not orders:
                return Response({'message': 'You do not have any order'}, status=status.HTTP_404_NOT_FOUND)
            
            # If ordering -> order by
            if ordering:
                orders = orders.order_by(ordering)
                
            page = paginator.paginate_queryset(orders, request)
            serializer = OrderSerializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            return paginated_response
        
    # POST method and check the role
    elif request.method == 'POST' and customer_group in user_roles:
        # Create a new order item for the current user
        # Get current cart items
        cart_items = Cart.objects.all().filter(user_id=request.user.id)
        
        # If there are no items in the cart
        if cart_items.count() == 0:
            return Response({'message': 'There are no items in the cart'}, status=status.HTTP_404_NOT_FOUND)
        
        # Count total value of the order
        total_value = 0
        for i in cart_items.values():
            total_value += i['price']
            
        # Create the order
        order = Order(
            user = request.user,
            total = total_value
        )
        order.save()
        
        # Add cart items to the order items table
        for i in cart_items.values():
            order_item = OrderItem(
                order = order,
                menuitem_id = i['menuitem_id'],
                quantity = i['quantity'],
                unit_price = i['unit_price'],
                price = i['price']
            )
            order_item.save()
            
        # Delete all items from the cart for this user
        Cart.objects.filter(user=request.user).delete()
        
        return Response({'message': 'The order has been placed'}, status=status.HTTP_201_CREATED)

    else:
        return Response({'message': 'You are not authorized to do this operation'}, status=status.HTTP_403_FORBIDDEN)
        
        
# Allow only token authenticated users
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_detailed(request, orderId):
    
    # Check roles of the user
    try:
        user_roles = request.user.groups.all()
    except AttributeError:
        return Response({'message': 'User without a role'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Get all groups
    manager_group = Group.objects.get(name='Manager')
    delivery_crew_group = Group.objects.get(name='Delivery Crew')
    customer_group = Group.objects.get(name='Customer')
    
    # Get method and check the role
    if request.method == 'GET' and customer_group in user_roles:
        
        # Get all items of this order ID
        order_items = OrderItem.objects.all().filter(order_id=orderId)
        if not order_items:
            return Response({'message': 'The order does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the order belongs to the right user
        order_user = order_items.first().order.user_id
        if request.user.id != order_user:
            return Response({'message': 'This order belongs to another user'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PUT method and check the role
    elif request.method == 'PUT' and manager_group in user_roles:
        # Update or create the order
        # Get all the necessary fields
        data = request.data
        
        # Retrieve the right order
        try:
            order = Order.objects.get(id=orderId)
        except Order.DoesNotExist:
            return Response({'message': 'The order has not been found'}, status=status.HTTP_404_NOT_FOUND)
            # Alternative approach - update instead of 404
            # data['id'] = orderId
            # serializer = OrderSerializer(data=data)
            # if serializer.is_valid():
            #     serializer.save()
            #     return Response(serializer.data, status=status.HTTP_200_OK)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
        # Update the order with the new data
        serializer = OrderSerializer(order, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PATCH method
    elif request.method == 'PATCH' and (manager_group in user_roles or delivery_crew_group in user_roles):
        
        # Retrieve the right order
        try:
            order = Order.objects.get(id=orderId)
        except Order.DoesNotExist:
            return Response({'message': 'The order has not been found'}, status=status.HTTP_404_NOT_FOUND)

        # Qualify user to the right role
        
        # Update the order (Set a delivery crew to this order and update the order status)
        if manager_group in user_roles:
                        
            # Update the order
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the order (possible to change only the order status)
        elif delivery_crew_group in user_roles:
            
            # Check if the order belongs to the right employee
            if order.delivery_crew_id != request.user.id:
                return Response({'message': 'This order belongs to the other delivery crew'})
            
            # Retrieve the status
            try:
                order_status = request.data['status']
            except KeyError:
                return Response({'message': 'The status has not been provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the order
            serializer = OrderSerializer(order, data={'status': order_status}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE method and check the role
    elif request.method == 'DELETE' and manager_group in user_roles:
        # Retrieve the right order
        try:
            order = Order.objects.get(id=orderId)
        except Order.DoesNotExist:
            return Response({'message': 'The order has not been found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the order
        order.delete()
        message = {'message': f'The order with id {orderId} has been succesfully deleted'}
        return Response(message, status=status.HTTP_200_OK)
    
    else:
        return Response({'message': 'You are not authorized to do this operation'}, status=status.HTTP_403_FORBIDDEN)