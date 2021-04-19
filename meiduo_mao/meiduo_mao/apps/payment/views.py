from django.shortcuts import render

from django.conf import settings
from django.views import View
from django import http
from alipay import AliPay
import os

from payment.models import Payment
from orders.models import OrderInfo
from meiduo_mao.utils.views import LoginRequiredJSONMixin
# Create your views here.


class PaymentStatusView(LoginRequiredJSONMixin, View):

    def get(self, request):
        query_dict = request.GET

        data = query_dict.dict()

        signature = data.pop('sign')

        app_private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")
        alipay_public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")
        with open(alipay_public_key_path) as pub:
            public = pub.read()

        with open(app_private_key_path) as pri:
            private = pri.read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=private,
            alipay_public_key_string=public,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        success = alipay.verify(data, signature)

        if success:
            order_id = data.get("out_trade_no")
            trade_id = data.get("trade_no")

            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )

            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            context = {
                "trade_id":trade_id
            }

            return render(request, 'pay_success.html', context)

        else:
            return http.HttpResponseForbidden("非法请求")




class PaymentView(LoginRequiredJSONMixin, View):

    def get(self, request, order_id):

        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单信息错误')

        app_private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")
        alipay_public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")
        with open(alipay_public_key_path) as pub:
            public = pub.read()

        with open(app_private_key_path) as pri:
            private = pri.read()


        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=private,
            alipay_public_key_string=public,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'alipay_url': alipay_url})


