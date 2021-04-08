from django.shortcuts import render

from django.views import View


from goods.models import GoodsChannelGroup, GoodsChannel, GoodsCategory
# Create your views here.

class IndexView(View):

    def get(self, request):

        categories = {}
        channels = GoodsChannel.objects.all()
        for channel in channels:
            group_id = channel.group_id
            if group_id not in categories.keys():
                categories[group_id] = {"channels": [], "sub_cats":[]}

            cat1 = channel.category

            categories[group_id]["channels"].append({
                "id": cat1.id,
                "name": cat1.name,
                "url": channel.url
            })

            for cat2 in cat1.subs.all():
                cat2.sub_cats = []
                for cat3 in cat2.subs.all():
                    cat2.sub_cats.append(cat3)

                categories[group_id]["sub_cats"].append(cat2)

        context = {
            "categories":categories
        }

        return render(request, 'index.html', context)


