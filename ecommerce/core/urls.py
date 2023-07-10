from django.urls import path
from core import views
from core.views import *
from accounts.views import *
from .views import *


urlpatterns = [
    
    path('',views.index,name='index'),
    path('about/',About.as_view(),name='about'),
    path('contact/',Contact.as_view(),name='contact'),
    path('add_product',Add_Product.as_view(),name='add_product'),
    path('product_desc/<int:pk>',Product_Desc.as_view(),name='product_desc'), 
    path('add_to_cart/<pk>',Add_To_Cart.as_view(),name="add_to_cart"),
    path('orderlist',Orderlist.as_view(),name="orderlist"),
    path('add_item/<int:pk>',Add_item.as_view(),name="add_item"),
    path('orders',OrderListView.as_view(),name='orders'),
    path("remove_item/<int:pk>", views.remove_item, name="remove_item"),
    path("checkout_page", views.checkout_page, name="checkout_page"),
    path("payment", views.payment, name="payment"),
    path("handlerequest", views.handlerequest, name="handlerequest"),
    path("render_pdf_view",views.render_pdf_view, name="render_pdf_view"),
    path('orders/cancel/<int:id>',cancelorder,name='cancel'),
    path('search/',views.search,name='search')
    
]