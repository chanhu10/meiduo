#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/9 20:12
from collections import OrderedDict

from goods.models import GoodsChannel


def get_category():
    categories = OrderedDict()
    channels = GoodsChannel.objects.all()
    for channel in channels:
        group_id = channel.group_id
        if group_id not in categories.keys():
            categories[group_id] = {"channels": [], "sub_cats": []}

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

    return categories


def get_breadcrumb(category):

    breadcrumb = {
        "cat1": '',
        "cat2": '',
        "cat3": '',
    }

    if category.parent == None:
        breadcrumb['cat1'] = category

    elif category.subs.count() == 0:
        cat2 = category.parent
        breadcrumb['cat1'] = cat2.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat3'] = category

    else:
        breadcrumb['cat1'] = category.parent
        breadcrumb['cat2'] = category

    return breadcrumb

