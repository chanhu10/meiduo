from django.shortcuts import render

from django import http
from django.views import View
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from datetime import datetime

from goods.utils import get_category, get_breadcrumb
from goods.models import GoodsCategory, SKU, GoodsVisitCount
# Create your views here.


class DetailVisitView(View):

    def post(self, request, category_id):

        # 接受和校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden("category_id不存在")

        # 获取当天的日期
        t = timezone.localtime()
        today_str = "%d-%02d-%02d" % (t.year, t.month, t.day)
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        # 统计指定分类商品的访问量
        try:
            count_data = GoodsVisitCount.objects.get(date=today_date, category=category)
        except GoodsVisitCount.DoesNotExist:
            count_data = GoodsVisitCount()
        try:
            count_data.category = category
            count_data.count += 1
            count_data.date = today_date
            count_data.save()
        except Exception as e:
            raise e

        # 响应结果

        return http.JsonResponse({"code": 0, "errmsg": "ok"})


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情页"""
        #"接受和校验参数"
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return render(request, "404.html")

        # 查询商品分类
        categories = get_category()

        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 构造上下文
        context = {
            "categories": categories,
            "breadcrumb": breadcrumb,
            "sku": sku,
            'specs': goods_specs
        }



        return render(request, 'detail.html', context)



class HotGoodsView(View):

    def get(self, request, category_id):
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        hot_skus = []
        for sku in skus:
            sku_dict= {
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "default_image_url": sku.default_image.url
            }
            hot_skus.append(sku_dict)

        return http.JsonResponse({"code": 0, "errmsg": "ok", "hot_skus": hot_skus})




class ListView(View):

    def get(self, request, category_id, page_num):

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden("参数不存在")

        sort = request.GET.get('sort', 'default')
        if sort == "price":
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'
        else:
            sort = "default"
            sort_field = 'create_time'

        categories = get_category()

        breadcrumb = get_breadcrumb(category)

        # skus = SKU.objects.filter(category=category, is_launched=True)

        skus = category.sku_set.filter(is_launched=True).order_by(sort_field)

        paginator = Paginator(skus,5)
        try:
            page_skus = paginator.page(page_num)

        except EmptyPage:
            return http.HttpResponseForbidden("EmptyPage")

        total_page = paginator.num_pages


        context = {
            "categories": categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            "total_page": total_page,
            "sort": sort,
            "category": category,
            'page_num': page_num

        }

        return render(request, "list.html", context)

