#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/9 19:51

from django.urls import path
from . import views



urlpatterns = [
    path('list/<int:category_id>/<int:page_num>/', views.LisyView.as_view(), name='list'),

]