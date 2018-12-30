from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.urls import reverse
from django.core.paginator import Paginator

from apps.goods.models import IndexActivityBanner, IndexPromotionGoods, IndexRecommendGoods, GoodsSKU, IndexFeaturedGoods, GoodsType
from apps.order.models import OrderGoods


class IndexView(View):
    '''首页'''
    def get(self, request):
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print('设置缓存')
            # 获取首页轮播商品信息
            bannerList = IndexActivityBanner.objects.all().order_by('index')[0:2]

            # 获取首页促销商品信息
            promotionList = IndexPromotionGoods.objects.all().order_by('index')[0:2]

            # 获取首页推荐商品信息
            recommendGoods = IndexRecommendGoods.objects.all().order_by('index')[0]

            # 获取首页最新商品信息
            newList = GoodsSKU.objects.all().order_by('-create_time')[0:5]

            # 获取首页最热商品信息
            hotList = GoodsSKU.objects.all().order_by('-sales')[0:5]

            # 获取首页特色商品信息
            featuredList = IndexFeaturedGoods.objects.all().order_by('index')[0:4]

            context = {
                'bannerList': bannerList,
                'promotionList': promotionList,
                'recommendGoods': recommendGoods,
                'newList': newList,
                'hotList': hotList,
                'featuredList': featuredList,
            }
            # 设置缓存
            cache.set('index_page_data', context, 3600)

        # 获取购物车商品数目
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)
        return render(request, 'index.html', context)


# goods/id
class DetailView(View):
    '''商品详情页'''
    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品的评论信息
        sku_orderGoods = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取同种类新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[0:4]

        # 获取购物车商品数目
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
            # 添加用户浏览历史记录
            history_key = 'history_%d' % user.id
            # 移除列表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入到列表左处
            conn.lpush(history_key, goods_id)
            # 只保留5条记录
            conn.ltrim(history_key, 0, 4)

        context = {
            'sku': sku,
            'sku_orderGoods': sku_orderGoods,
            'new_skus': new_skus,
            'cart_count': cart_count
        }
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式
# list/种类id/页码?sort=排序方式
class ListView(View):
    def get(self, request, type_id, page):
        # 先获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        # 获取排序方式：default， price，hot
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 获取购物车商品数目
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 获取分页数据
        paginator = Paginator(skus, 6)
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        skus_page = paginator.page(page)
        # 进行页码控制
        # 1.总页数小于5页,则显示所有页码
        # 2.如果当前页是前3页码,显示1-5
        # 3.如果当前页是后3页码,显示后5页
        # 4.显当前页的前两页,后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)
        context = {
            'type': type,
            'cart_count': cart_count,
            'skus_page': skus_page,
            'sort': sort,
            'pages': pages
        }
        return render(request, 'list.html', context)
