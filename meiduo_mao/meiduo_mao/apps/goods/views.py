from django.shortcuts import render

from django import http
from django.views import View

from goods.utils import get_category, get_breadcrumb
from goods.models import GoodsCategory
# Create your views here.

class LisyView(View):

    def get(self, request, category_id, page_num):

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden("参数不存在")

        categories = get_category()

        cat2 = category.parent

        breadcrumb = get_breadcrumb(category)

        context = {
            "categories": categories,
            'breadcrumb': breadcrumb
        }

        return render(request, "list.html", context)

