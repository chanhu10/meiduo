from django.views import View
from django_redis import get_redis_connection
from django import http
import logging
import random

from verifications.lib.captcha.captcha import captcha
from . import constants
from meiduo_mao.utils.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms_code

# Create your views here.
logger = logging.getLogger("django")


class SMSCodeView(View):

    def get(self, request, mobile):
        """

        :param request:
        :param mobile:
        :return:
        """

        # 接受参数
        image_code_client = request.GET.get("image_code")
        uuid = request.GET.get("uuid")
        print(uuid)
        # 校验参数

        if not all([image_code_client, uuid]):

            return http.HttpResponseForbidden("缺少必要参数")

        # 提取图形验证码
        redis_coon = get_redis_connection("verify_code")

        image_code_server = redis_coon.get(uuid)
        print(image_code_server)
        if image_code_server is None:
            return http.JsonResponse({"code":RETCODE.IMAGECODEERR, "errmsg":"图形验证码已过期"})

        # 删除图形验证码
        redis_coon.delete(uuid)

        # 对比图形验证码
        image_code_server = image_code_server.decode() #Redis，存进去的是二进制，拿出来的也是二进制
        if image_code_client.lower() != image_code_server.lower(): #全部转化为小写再比较，优化用户体验
            return http.JsonResponse({"code":RETCODE.IMAGECODEERR, "errmsg": "输入的图形验证码有误"})
        #
        send_flag = redis_coon.get(f"sms_{mobile}")
        if send_flag:
            return http.JsonResponse({"code":RETCODE.THROTTLINGERR, "errmsg":"发送短信过于频繁"})
        #
        # 生成短信验证码
        sms_code = str(random.randint(0, 999999)).rjust(6, '0')
        logger.info(sms_code)

        # 保存短信验证码
        pl = redis_coon.pipeline()
        pl.setex(name=mobile, time=constants.SMS_CODE_REDIS_EXPIRES, value=sms_code)
        pl.setex(name=f"sms_{mobile}", time=constants.SEND_SMS_CODE_INTERVAL, value=1)
        pl.execute()

        # 发送短信
        # CCP().send_message(tid="1", mobile=mobile, datas=(sms_code, "5"))
        send_sms_code.delay(mobile, sms_code)




        # 响应结果
        return http.JsonResponse({"code":RETCODE.OK, "errmsg": "发送短信成功"})



class ImageCodeView(View):

    def get(self, request, uuid):

        # 生成验证码

        text, image = captcha.generate_captcha()

        # 存到redis
        redis_conn = get_redis_connection("verify_code")
        redis_conn.setex(name=uuid, time=3000, value=text)

        # 返回图片验证码
        return http.HttpResponse(image, content_type="image/jpg")

