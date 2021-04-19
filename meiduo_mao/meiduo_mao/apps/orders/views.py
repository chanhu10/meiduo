from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django_redis import get_redis_connection
from decimal import Decimal
import json
from django import http
from django.utils import timezone
from django.db import transaction

from users.models import Address
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from meiduo_mao.utils.views import LoginRequiredJSONMixin

# Create your views here.


class OrderSuccessView(LoginRequiredMixin, View):

    def get(self, request):
        order_id = request.GET.get("order_id")
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            "order_id": order_id,
            "payment_amount": payment_amount,
            "pay_method": pay_method
        }

        return render(request, "order_success.html", context)


class OrderCommitView(LoginRequiredJSONMixin, View):
    """提交订单"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        # 获取当前要保存的订单数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 校验参数
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return http.HttpResponseForbidden('参数address_id错误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"], OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.HttpResponseForbidden("参数payment错误")

        # 开启事务
        with transaction.atomic():
            save_id = transaction.savepoint()

            try:
                user = request.user
                order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ("%09d" % user.id)

                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=0,
                    freight=Decimal(10.00),
                    pay_method=pay_method,
                    status= OrderInfo.ORDER_STATUS_ENUM["UNPAID"] if pay_method==OrderInfo.PAY_METHODS_ENUM["ALIPAY"] else OrderInfo.ORDER_STATUS_ENUM["UNSEND"]

                )

                redis_conn = get_redis_connection('carts')

                redis_cart = redis_conn.hgetall('carts_%s' % user.id)

                redis_selected = redis_conn.smembers('selected_%s' % user.id)

                # 构造购物车中 被选中商品的数据
                new_cart_dict = {}
                for sku_id in redis_selected:
                    new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

                # 获取被勾选商品的sku_id
                sku_ids = new_cart_dict.keys()
                for sku_id in sku_ids:

                    while True:
                        sku = SKU.objects.get(id=sku_id)#这里不能用缓存，需要实时查询，所以没用filter

                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        sku_count = new_cart_dict[sku.id]

                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({"code": 0,"errmsg": "库存不足"})

                        # # SKU 减库存 加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        new_stock=origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)

                        if result == 0:
                            continue


                        # SPU 加销量
                        sku.spu.sales += sku_count
                        sku.spu.save()

                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price

                        break

                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_id)

                return http.JsonResponse({"code": 0, "errmsg": "下单失败"})

            transaction.savepoint_commit(save_id)


        return http.JsonResponse({"code":0, "errmsg":"ok", "order_id":order_id})




class OrderSettlementView(LoginRequiredMixin, View):
    """结算订单"""

    def get(self, request):
        """提供订单结算页面"""

        user = request.user

        # 收货地址

        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 购物车

        redis_conn = get_redis_connection('carts')

        redis_cart = redis_conn.hgetall('carts_%s' % user.id)

        redis_selected = redis_conn.smembers('selected_%s' % user.id)

        # 构造购物车中 被选中商品的数据
        new_cart_dict = {}
        for sku_id in redis_selected:
            new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

        sku_ids = new_cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        total_count = 0
        total_amount = Decimal(0.00)
        for sku in skus:
            sku.count = new_cart_dict[sku.id]
            sku.amount = sku.price * sku.count

        total_count += sku.count
        total_amount += sku.amount

        freight = Decimal(10.00)


        context = {
            "addresses": addresses,
            'skus': skus,
            "total_count": total_count,
            "total_amount": total_amount,
            "freight": freight,
            "payment_amount": total_amount + freight,
        }


        return render(request, 'place_order.html', context)