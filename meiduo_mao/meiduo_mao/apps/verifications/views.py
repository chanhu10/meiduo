from django.shortcuts import render

from django.views import View
# Create your views here.
from django_redis import get_redis_connection
from django import http

from verifications.lib.captcha.captcha import captcha
from . import constants

class ImageCodeView(View):

    def get(self, request, uuid):

        # 生成验证码

        text, image = captcha.generate_captcha()

        # 存到redis
        redis_conn = get_redis_connection("verify_code")
        redis_conn.setex(name=uuid, time=constants.IMAGE_CODE_REDIS_EXPIRES, value=text)

        # 返回图片验证码
        return http.HttpResponse(image, content_type="image/jpg")

