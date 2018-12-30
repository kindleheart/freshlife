from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime
from django.conf import settings
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import OrderInfo, OrderGoods

from utils.mixin import LoginRequiredMixin
from alipay import AliPay
import os


# /order/place
class OrderPlaceView(LoginRequiredMixin, View):
    '''提交订单页面显示'''
    def post(self, request):
        user = request.user

        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect(reverse('cart:info'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        # 商品总件数,总价格
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            # 动态获取用户购买的数量
            count = conn.hget(cart_key, sku_id)
            count = int(count)
            # 计算商品小计
            amount = sku.price * count
            # 动态给商品增加属性
            sku.count = count
            sku.amount = amount
            skus.append(sku)
            total_count += count
            total_price += amount
        # 运费,如果运费不下于88,无运费, 否则20元运费
        transit_price = 0
        if total_price < 88:
            transit_price = 20
        # 实付款
        total_pay = total_price + transit_price

        # 获取用户收件地址
        addrs = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)

        # 获取用户浏览记录
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hlen(cart_key)

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
            'cart_count': cart_count
        }
        return render(request, 'place_order.html', context)


# 订单创建基于事物,一组sql操作要么都成功要么都失败
# 并发控制
# 前段接受参数:addr_id pay_method sku_ids
# /order/commit
class OrderCommitView(View):
    '''订单创建'''
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 校验参数完整性
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # todo: 创建订单核心业务
        # 1.订单编号
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 2.总数目和总费用
        total_count = 0
        total_price = 0
        # 3.运费
        transit_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()
        try:
            # todo: 向订单表中添加一条信息
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)
            # todo: 向订单商品表添加多条记录
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            for sku_id in sku_ids:
                # 给三次机会尝试重新购买
                for i in range(3):
                    try:
                        # 加上悲观锁 for update
                        # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    count = conn.hget(cart_key, sku_id)
                    count = int(count)
                    # todo: 判断库存
                    if count > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 更新商品的库存和销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - count
                    new_sales = sku.sales + count

                    # 乐观锁
                    # 返回受影响的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 更新失败
                            transaction.savepoint_rollback(sku_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        continue

                    # todo: 添加订单商品
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)
                    # todo: 累加计算订单商品的总数量和总价格
                    amount = sku.price * count
                    total_count += count
                    total_price += amount

                    # 一次成功,跳出循环
                    break

            if total_price < 88:
                transit_price = 20

            # todo: 更新订单信息表中的总数量总价格和邮费
            order.total_count = total_count
            order.total_price = total_price
            order.transit_price = transit_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败1'})

        # 提交事物
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中的记录,sku_ids 需要拆包[1,3]->1,3
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'message': '创建成功'})


# 订单支付
# 前端接收参数: 订单id(order_id)
# /order/pay
class OrderPayView(View):
    '''订单支付'''
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接受参数
        order_id = request.POST.get('order_id')
        # 检验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理: 使用python sdk, 调用支付宝接口
        # 初始化
        alipay = AliPay(
            appid="2016092300575928",  # 应用ID
            app_notify_url=None,  # 默认回调url
            app_private_key_string=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        print(1111111111111)
        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal不能序列化,需要转化为字符串
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 订单总金额
            subject='freshlife%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})




