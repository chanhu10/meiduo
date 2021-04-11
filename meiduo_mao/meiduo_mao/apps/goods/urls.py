#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/9 19:51

from django.urls import path, re_path
from . import views

urlpatterns = [
    # re_path('list/(?P<category_id>[0-9]+)/(?P<page_num>[0-9]+)/$', views.ListView.as_view(), name='list'),
    path('list/<int:category_id>/<int:page_num>/', views.ListView.as_view(), name='list'),

    path('hot/<int:category_id>/', views.HotGoodsView.as_view()),

]