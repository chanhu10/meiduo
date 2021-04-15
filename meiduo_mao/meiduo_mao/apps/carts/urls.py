#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/15 19:19

from django.urls import path
from . import views


urlpatterns = [
    path('carts/', views.CartsView.as_view(), name='info'),
    path('carts/selection/', views.CartsSelectAllView.as_view()),

]