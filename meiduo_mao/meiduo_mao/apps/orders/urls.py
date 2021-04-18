#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/9 19:51

from django.urls import path, re_path
from . import views

urlpatterns = [

    path('orders/settlement/', views.OrderSettlementView.as_view(), name='settlement'),
    path('orders/commit/', views.OrderCommitView.as_view(), name='commit'),
    path('orders/success/', views.OrderSuccessView.as_view(),name='info'),

]