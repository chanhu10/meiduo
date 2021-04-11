from django.shortcuts import render

from django import http
from django.views import View
from django.core.paginator import Paginator, EmptyPage

from goods.utils import get_category, get_breadcrumb
from goods.models import GoodsCategory, SKU
# Create your views here.


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

