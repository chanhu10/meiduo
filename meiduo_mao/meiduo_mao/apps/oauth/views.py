from django.shortcuts import render
from django.views import View
from django.conf import settings
from django import http
import logging
import re
from django_redis import get_redis_connection
from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.shortcuts import redirect, reverse


from oauth.models import OAUthQQUser
from meiduo_mao.utils.response_code import RETCODE
from oauth.utils import generate_access_token, check_access_token
from users.models import User
# Create your views here.


logger = logging.getLogger("django")


class QQAuthUserView(View):

    def get(self, request):

        code = request.GET.get("code")

        if not code:
            return http.HttpResponseForbidden("缺少code")

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        try:
            access_toke = oauth.get_access_token(code)

            openid = oauth.get_open_id(access_toke)
        except Exception as e:
            logger.error(e)

            return http.HttpResponseServerError("oauth2.0认证失败")

        # 判断openid是否绑定过用户
        try:
            oauth_user = OAUthQQUser.objects.get(openid=openid)
        except OAUthQQUser.DoesNotExist:
            # openid 未绑定用户
            access_toke_openid = generate_access_token(openid)
            context = {"access_toke_openid": access_toke_openid}
            return render(request, 'oauth_callback.html', context)
        else:
            # openid已经绑定用户
            login(request, oauth_user.user)

            response = redirect(reverse('contents:index'))

            response.set_cookie('username', oauth_user.user.username, max_age=3600 * 24 * 15)

            return response

    def post(self, request):

        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        sms_code_client = request.POST.get("sms_code")
        access_toke_openid = request.POST.get("access_toke_openid")

        if not all([mobile,password,sms_code_client]):
            return http.HttpResponseForbidden("缺少必要参数")

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden("请输入正确的手机号码")

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden("请输入8-20位的密码")

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get(mobile)
        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg':"无效的短信验证码"})

        if sms_code_client != sms_code_client:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': "输入的验证码错误"})

        openid = check_access_token(access_toke_openid)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': "openid已失效"})

        # 使用手机号查询，用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, password=password,mobile=mobile)
        else:
            if not user.check_password(password):
                return render(request,'oauth_callback.html', {"account_errmsg":"账号或密码错误"})

        try:
            oauth_qq_user = OAUthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            logger.error(e)
            return render(request, 'oauth_callback.html', {'qq_login_errmsg':"账号或密码错误"})

        # 实现状态保持
        login(request, oauth_qq_user.user)

        # 重定向到首页
        next = request.GET.get('state')
        response = redirect(next)

        # cookie中写入用户名
        response.set_cookie('username',oauth_qq_user.user.username, max_age=3600*24*15)

        return response









class QQAuthURLView(View):

    def get(self, request):

        next = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        login_url = oauth.get_qq_url()

        return http.JsonResponse({"code":RETCODE.OK,"errmsg":"ok","login_url":login_url})