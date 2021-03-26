#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/3/26

from django.urls import path


from . import views

urlpatterns = [

    path('areas/', views.AreasView.as_view(), name="haha"),

]


