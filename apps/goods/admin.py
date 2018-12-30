from django.contrib import admin
from apps.goods.models import GoodsType, GoodsImage, GoodsSKU, GoodsSPU, IndexActivityBanner,\
    IndexPromotionGoods, IndexRecommendGoods, IndexFeaturedGoods


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或者更新数据时调用'''
        super().save_model(request, obj, form, change)

        # 重新发出任务，重新生成静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        '''删除表中数据时调用'''
        super().delete_model(request, obj)

        # 重新发出任务，重新生成静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class GoodsSPUAdmin(BaseModelAdmin):
    pass


class GoodsSKUAdmin(BaseModelAdmin):
    pass


class GoodsImageAdmin(BaseModelAdmin):
    pass


class IndexActivityBannerAdmin(BaseModelAdmin):
    pass


class IndexPromotionGoodsAdmin(BaseModelAdmin):
    pass


class IndexRecommendGoodsAdmin(BaseModelAdmin):
    pass


class IndexFeaturedGoodsAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(GoodsSPU, GoodsSPUAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)
admin.site.register(IndexActivityBanner, IndexActivityBannerAdmin)
admin.site.register(IndexPromotionGoods, IndexPromotionGoodsAdmin)
admin.site.register(IndexRecommendGoods, IndexRecommendGoodsAdmin)
admin.site.register(IndexFeaturedGoods, IndexFeaturedGoodsAdmin)


