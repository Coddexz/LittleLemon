from django.urls import path, re_path
from . import views


urlpatterns = [
    path('category', views.CategoryView.as_view(), name='cateogry'),
    path('menu-items', views.MenuItems.as_view(), name='menu_items'),
    path('menu-items/<int:pk>', views.MenuItemsDetail.as_view(), name='item_of_menu'),
    re_path(r'^groups/(?P<group>manager|delivery-crew)/users$', views.GroupManagement.as_view(
        {'get': 'list', 'post': 'create'}), name='group_list_create'),
    re_path(r'^groups/(?P<group>manager|delivery-crew)/users/(?P<id>\d+)$', views.GroupManagementDelete.as_view(
        {'delete': 'destroy'}), name='group_list_delete'),
    path('cart/menu-items', views.cart_items, name='cart_items'),
    path(('orders'), views.order, name='orders'),
    path('orders/<int:orderId>', views.order_detailed, name='orders_detailed'),
]