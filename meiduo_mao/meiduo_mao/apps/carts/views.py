from django.shortcuts import render

from django.views import View
from django import http
from django_redis import get_redis_connection

import json
import base64
import pickle


from goods.models import SKU
# Create your views here.


class CartsView(View):

    def post(self, request):

        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get("sku_id")
        count = json_dict.get("count")
        selected = json_dict.get("selectes", True)

        # 校验参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden("缺少参数")

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数SKU错误")

        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden("参数count错误")

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden("参数selected错误")
        # 判断用户是否登录

        user = request.user

        if user.is_authenticated:
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s'%user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s'%user.id, sku_id)
            pl.execute()

            return http.JsonResponse({"code": 0, "errmsg": "ok"})

        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                origin_count = cart_dict["sku_id"]["count"]
                count += origin_count

            cart_dict[sku_id] = {
                "count": count,
                "selected": selected
            }

            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_cart_str = cart_str_bytes.decode()


            resopnse = http.JsonResponse({"code": 0, "errmsg": "ok"})
            resopnse.set_cookie("carts", cookie_cart_str)

            return resopnse


    def get(self, request):

        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection("carts")
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            redis_selected = redis_conn.smembers('selected_%s' % user.id)

            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in redis_selected
                }
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()

        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * cart_dict.get(sku.id).get('count')),
            })

        context = {
            'cart_skus': cart_skus,
        }

        return render(request, "cart.html", context)


    def put(self, request):

        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get("sku_id")
        count = json_dict.get("count")
        selected = json_dict.get("selectes", True)

        # 校验参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden("缺少参数")

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数SKU错误")

        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden("参数count错误")

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden("参数selected错误")
        # 判断用户是否登录

        user = request.user

        if user.is_authenticated:

            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()

            pl.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s'%user.id, sku_id)
            else:
                pl.srem('selected_%s'%user.id, sku_id)

            pl.execute()

            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return http.JsonResponse({'code': 0, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        else:
            # 用户未登录，修改cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # 覆盖写入
            cart_dict[sku_id] = {
                "count": count,
                "selected": selected
            }
            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }


            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_cart_str = cart_str_bytes.decode()

            resopnse = http.JsonResponse({"code": 0, "errmsg": "ok", 'cart_sku': cart_sku})
            resopnse.set_cookie("carts", cookie_cart_str)

            return resopnse



    def delete(self, request):

        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        # 判断用户是否登录
        user = request.user
        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()

            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s'%user.id, sku_id)
            pl.execute()

            return http.JsonResponse({"code": 0, "errmsg": "ok"})

        else:
            # 用户未登录，删除cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            resopnse = http.JsonResponse({"code": 0, "errmsg": "ok"})

            if sku_id in cart_dict:
                del cart_dict[sku_id]

                cart_dict_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                cookie_cart_str = cart_str_bytes.decode()

                resopnse.set_cookie("carts", cookie_cart_str)

            return resopnse


        pass









