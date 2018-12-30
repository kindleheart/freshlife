from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


class GoodsType(BaseModel):
    '''商品种类'''
    name = models.CharField(max_length=20, verbose_name='种类名称')

    class Meta:
        db_table = 'fl_goods_type'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSKU(BaseModel):
    '''商品SKU'''
    status_choices = (
        (0, '下线'),
        (1, '上线'),
    )
    type = models.ForeignKey('GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    goods = models.ForeignKey('GoodsSPU', verbose_name='商品SPU', on_delete=models.CASCADE)
    name = models.CharField(max_length=20, verbose_name='商品名称')
    simple_desc = models.CharField(max_length=100, default='', verbose_name='商品简介')
    desc = HTMLField(blank=True, verbose_name='商品详情')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    prime_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品原价')
    unite = models.CharField(max_length=20, verbose_name='商品单位')
    image = models.ImageField(upload_to='goods', verbose_name='商品图片')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    status = models.SmallIntegerField(default=1, choices=status_choices, verbose_name='商品状态')

    class Meta:
        db_table = 'fl_goods_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSPU(BaseModel):
    '''商品SPU'''
    name = models.CharField(max_length=20, verbose_name='商品SPU名称')
    detail = HTMLField(blank=True, verbose_name='商品详情')

    class Meta:
        db_table = 'fl_goods_spu'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsImage(BaseModel):
    '''商品图片'''
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='goods', verbose_name='图片路径')

    class Meta:
        db_table = 'fl_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class IndexActivityBanner(BaseModel):
    '''首页轮播活动展示'''
    name = models.CharField(max_length=20, verbose_name='活动名称')
    desc = models.CharField(max_length=256, verbose_name='活动简介')
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='banner', verbose_name='活动图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'fl_index_banner'
        verbose_name = '首页轮播活动'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class IndexPromotionGoods(BaseModel):
    '''首页促销商品'''
    image = models.ImageField(upload_to='banner', verbose_name='商品图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)

    class Meta:
        db_table = 'fl_index_promotion'
        verbose_name = "主页促销商品"
        verbose_name_plural = verbose_name


class IndexRecommendGoods(BaseModel):
    '''首页推荐商品'''
    image = models.ImageField(upload_to='banner', verbose_name='商品图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)

    class Meta:
        db_table = 'fl_index_recommend'
        verbose_name = "主页推荐商品"
        verbose_name_plural = verbose_name


class IndexFeaturedGoods(BaseModel):
    '''首页特色商品'''
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)

    class Meta:
        db_table = 'fl_index_featured'
        verbose_name = "主页特色商品"
        verbose_name_plural = verbose_name
