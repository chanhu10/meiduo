#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/21 20:11


from django.template import loader
from django.conf import settings
import os
from collections import OrderedDict
from contents.models import ContentCategory
from goods.utils import get_category

def generate_static_index_html():

    categories = get_category()

    contents = OrderedDict()
    content_categoties = ContentCategory.objects.all()
    for content_categoty in content_categoties:
        contents[content_categoty.key] = content_categoty.content_set.filter(status=True).order_by("sequence")

    context = {
        "categories": categories,
        "contents": contents
    }

    template = loader.get_template("index.html")

    html_text = template.render(context)

    file_path = os.path.join(settings.STATICFILES_DIRS, "index.html")
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(html_text)

def generate_static_index_html2():

    data = "263847gudh3rh"
    file_path = os.path.join(settings.STATICFILES_DIRS, "index.html")

    with open(file_path, "w", encoding='utf-8') as f:
        f.write(data)



