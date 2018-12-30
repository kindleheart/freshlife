# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import  loader
# 在任务处理者一端添加该配置
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freshlife.settings')
django.setup()

# 必须在配置之后
from apps.goods.models import IndexActivityBanner, IndexPromotionGoods, IndexRecommendGoods, GoodsSKU, IndexFeaturedGoods

# 创建一个Celery对象
broker = 'redis://127.0.0.1:6379/0'
backend = 'redis://127.0.0.1:6379/1'
app = Celery('celery_tasks', broker=broker, backend=backend)


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    print('****************************')
    '''发送激活邮件'''
    subject = 'freshlife欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为freshlife注册会员</h1>请点击下面的链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">请点击此处激活</a>' % (username, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)

@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
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

    # 使用模板
    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(context)
    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    with open(save_path, 'w') as f:
        f.write(static_index_html)
