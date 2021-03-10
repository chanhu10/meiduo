from django.shortcuts import render

from django.views import View

from django import http

from django.shortcuts import redirect, reverse
import re

from meiduo_mao.utils.response_code import RETCODE
from users.models import User
from django.db import DatabaseError

from django.contrib.auth import login
# Create your views here.


class UsernameCountView(View):

    def get(self, request, username):
        """
        判断用户是否重复注册
        :param request:
        :param username: 用户名
        :return:
        """
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok", "count": count})


class Register(View):

    # 用户注册

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):

        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        mobile = request.POST.get("mobile")
        allow = request.POST.get("allow")

        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden("缺少必要参数")

        if not re.match(r'^[a-z0-9A-Z_-]{5,20}$', username):
            return http.HttpResponseForbidden("请输入5-20个字符的用户名")

        if not re.match(r'^[0-9a-zA-Z]{8,20}', password):
            return http.HttpResponseForbidden("请输入8-20位的密码")

        if not password == password2:
            return http.HttpResponseForbidden("2次输入的密码不一致")

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden("请输入正确的手机号")

        if allow != "on":
            return http.HttpResponseForbidden("请勾选用户协议")


        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            render(request, 'register.html', {"register_errmsg": "注册失败"})
        else:
            login(request, user)

        return redirect(reverse('contents:index'))



