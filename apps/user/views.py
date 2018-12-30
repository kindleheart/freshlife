from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection
from django.core.paginator import Paginator

from celery_tasks.tasks import send_register_active_email
from apps.user.models import User, Address
from apps.order.models import OrderInfo, OrderGoods
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from utils.mixin import LoginRequiredMixin
from apps.goods.models import GoodsSKU
import re


# /user/register
class RegisterView(View):
    '''注册类'''
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 校验是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': '用户已存在'})
        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/加密信息
        # 激活邮件中需要包含用户的身份信息，并且要把身份信息加密
        # 加密用户信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf-8')

        # 发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))


# 用户激活
class ActiveView(View):
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取带激活用户的id
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登入页面
            return render(request, 'index.html')
        except SignatureExpired:
            # 激活链接已过期
            return HttpResponse("激活链接已过期")


class LoginView(View):
    def get(self, request):
        '''显示登陆页面'''
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登入校验'''
        # 接收收据
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 数据校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理 登陆校验

        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 记录用户登陆状态
                login(request, user)
                # 获取登陆后跳转的地址
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到next_url
                response = redirect(next_url)
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=10*60)
                else:
                    response.delete_cookie('username')
                # 返回response
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogoutView(View):
    def get(self, request):
        '''退出登录'''
        # 清除 session 信息
        logout(request)
        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user=user)
        # 获取用户浏览记录
        conn = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        # 获取用户最新的5个商品的id
        sku_ids = conn.lrange(history_key, 0, 4)
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 获取购物车数量
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hlen(cart_key)

        context = {'address': address, 'goods_li': goods_li, 'cart_count': cart_count}
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单'''
    def get(self, request, page):
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order)
            for order_sku in order_skus:
                # 计算每个商品的小计
                amount = order_sku.count * order_sku.price
                order_sku.amount = amount

            # 动态给order增加属性,保存订单商品的信息
            order.order_skus = order_skus
            # 动态给order增加属性,保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 订单总价(包括邮费)
            order.total_price_with_transit = order.total_price + order.transit_price

        # 分页
        paginator = Paginator(orders, 2)

        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        order_page = paginator.page(page)
        # 进行页码控制
        # 1.总页数小于5页,则显示所有页码
        # 2.如果当前页是前3页码,显示1-5
        # 3.如果当前页是后3页码,显示后5页
        # 4.显当前页的前两页,后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 获取用户浏览记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hlen(cart_key)

        context = {
            'order_page': order_page,
            'pages': pages,
            'cart_count': cart_count
        }

        return render(request, 'user_center_order.html', context)


# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址'''
    def get(self, request):
        # 获取默认收货地址
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户浏览记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hlen(cart_key)

        context = {
            'address': address,
            'cart_count': cart_count
        }
        return render(request, 'user_center_address.html', context)

    def post(self, request):
        # 接受数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')

        # 获取默认收货地址
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户浏览记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hlen(cart_key)

        # 校验数据
        if not all([receiver, addr, phone]):
            context = {
                'errmsg': '数据不完整',
                'address': address,
                'cart_count': cart_count
            }
            return render(request, 'user_center_address.html', context)
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            context = {
                'errmsg': '手机格式不正确',
                'address': address,
                'cart_count': cart_count
            }
            return render(request, 'user_center_address.html', context)
        # 业务处理：地址添加
        # 如果用户已存在用户地址，添加的地址不作为默认收获地址，否则作为默认收货地址
        if address:
            is_default = False
        else:
            is_default = True
        Address.objects.create(user=user, receiver=receiver, addr=addr, postcode=postcode, phone=phone, is_default=is_default)

        return redirect(reverse('user:address'))


