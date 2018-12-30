from django.urls import path
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView, UserOrderView, AddressView

app_name = 'user'
urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),  # 用户注册
    path('active/<str:token>', ActiveView.as_view(), name='active'),  # 用户激活
    path('login', LoginView.as_view(), name="login"),  # 用户登录
    path('logout', LogoutView.as_view(), name='logout'),  # 用户退出

    path('info', UserInfoView.as_view(), name="user"),  # 用户中心-信息页
    path('order/<int:page>', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    path('address', AddressView.as_view(), name='address'),  # 用户中心-地址页
]
