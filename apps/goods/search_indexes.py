from haystack import indexes
from apps.goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
class GoodsSkuIndex(indexes.SearchIndex, indexes.Indexable):
    # text为索引字段 use_template指定根据表中的那些字段建立索引文件,把说明放在文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回模型类
        return GoodsSKU

    # 建立索引的数据
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
