from django.urls import path
from apps.cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = 'cart'
urlpatterns = [
    path('add', CartAddView.as_view(), name='add'),  # 添加购物车
    path('info', CartInfoView.as_view(), name='info'),  # 购物车详情
    path('update', CartUpdateView.as_view(), name='update'),  # 购物车记录更新
    path('delete', CartDeleteView.as_view(), name='delete')  # 购物车记录删除
]

