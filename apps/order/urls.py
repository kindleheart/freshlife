from django.urls import path
from apps.order.views import OrderPlaceView, OrderCommitView, OrderPayView
app_name = 'order'
urlpatterns = [
    path('place', OrderPlaceView.as_view(), name="place"),  # 提交订单页面显示
    path('commit', OrderCommitView.as_view(), name="commit"),  # 提交订单页面显示
    path('pay', OrderPayView.as_view(), name="pay")  # 订单支付
]
