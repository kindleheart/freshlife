from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

# 添加购物车
# 1) 请求方式：ajax post
# 2)  传递参数： 商品id(sku_id) 商品数量(count)


# /cart/add
class CartAddView(View):
    '''购物车记录添加'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 添加记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 如果sku_id在hash中不存在, hget返回none
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)
        # 校验是否超过库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存量不足'})
        # 设置hash中sku_id对应的值
        conn.hset(cart_key, sku_id, count)

        # 计算购物车商品的条目数
        cart_count = conn.hlen(cart_key)
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'message': '添加商品成功'})


# 购物车信息
# cart/info
class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 得到一个字典
        cart_dict = conn.hgetall(cart_key)
        skus = []
        # 保存用户购物车中的总数目和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品小计
            amount = sku.price*int(count)
            # 动态给商品增加属性
            sku.amount = amount
            sku.count = int(count)
            # 添加
            skus.append(sku)
            total_count += int(count)
            total_price += amount
        # 计算购物车商品的目数
        cart_count = conn.hlen(cart_key)
        context = {
            'total_count': total_count,
            'total_price': total_price,
            'skus': skus,
            'cart_count': cart_count
        }
        return render(request, 'cart.html', context)


# cart/update
# 购物车记录更新
class CartUpdateView(LoginRequiredMixin, View):
    '''购物车记录更新'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 更新购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 校验是否超过库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存量不足'})
        # 设置hash中sku_id对应的值
        conn.hset(cart_key, sku_id, count)
        # 计算购物车商品的总件数
        cart_count = conn.hlen(cart_key)
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 5, 'total_count': total_count, 'cart_count': cart_count, 'message': '更新成功'})


# 删除购物车记录
# /cart/delete
class CartDeleteView(View):
    def post(self, request):
        '''购物车记录删除'''
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        sku_id = request.POST.get('sku_id')
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hdel(cart_key, sku_id)

        # 计算购物车商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        return JsonResponse({'res': 3, 'total_count': total_count, 'message': '删除成功'})
