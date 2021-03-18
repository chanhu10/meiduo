from django.shortcuts import render

from django.views import View

from django import http

from django.shortcuts import redirect, reverse
import re
from django_redis import get_redis_connection

from meiduo_mao.utils.response_code import RETCODE
from users.models import User
from django.db import DatabaseError

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):

        return render(request, 'user_center_info.html')


class LogoutView(View):

    def get(self, request):

        # 退出登录
        logout(request)

        response = redirect(reverse('contents:index'))
        # 删除session
        response.delete_cookie('username')

        return response


class LoginView(View):

    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):

        # 接受参数
        username = request.POST.get("username")
        password = request.POST.get("password")
        remembered = request.POST.get("remembered")

        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden("缺少必要参数")

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden("请输入正确的用户名或手机号")

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden("请输入8到20位的密码")

        # 认证用户,判断用户是否存在
        user = authenticate(username=username, password=password)

        if user is None:
            return render(request, 'login.html', {"account_errmsg": "账号或密码错误"})

        # 登录
        login(request, user)

        # 状态保持
        if remembered == "on":
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)

        next = request.GET.get(next)
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        # 跳转到首页

        # response = redirect(reverse('contents:index'))

        response.set_cookie("username", username, expires=3600 * 24 * 15)

        return response


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
        sms_code_client = request.POST.get("sms_code")
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

        redis_conn = get_redis_connection("verify_code")
        sms_code_server = redis_conn.get(mobile)

        if sms_code_server is None:
            return render(request, 'register.html', {"sms_code_errms":"无效的短信验证码"})

        elif sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {"sms_code_errmsg":"输入的短信验证码有误"})

        if allow != "on":
            return http.HttpResponseForbidden("请勾选用户协议")

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            render(request, 'register.html', {"register_errmsg": "注册失败"})
        else:
            login(request, user)

        response = redirect(reverse('contents:index'))

        response.set_cookie("username", username, expires=3600 * 24 * 15)

        return response



