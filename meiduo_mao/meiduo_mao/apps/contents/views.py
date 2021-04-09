from django.shortcuts import render

from django.views import View
from collections import OrderedDict


from goods.models import GoodsChannelGroup, GoodsChannel, GoodsCategory
from contents.models import ContentCategory
from goods.utils import get_category
# Create your views here.

class IndexView(View):

    def get(self, request):

        categories = get_category()

        contents = OrderedDict()
        content_categoties = ContentCategory.objects.all()
        for content_categoty in content_categoties:
            contents[content_categoty.key] = content_categoty.content_set.filter(status=True).order_by("sequence")

        context = {
            "categories":categories,
            "contents":contents
        }

        return render(request, 'index.html', context)


