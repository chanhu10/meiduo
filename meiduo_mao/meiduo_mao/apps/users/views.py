from django.shortcuts import render

from django.views import View

from django import http

from django.shortcuts import redirect, reverse
import re
import json
import logging
from django_redis import get_redis_connection

from meiduo_mao.utils.response_code import RETCODE
from users.models import User
from django.db import DatabaseError

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from meiduo_mao.utils.response_code import RETCODE
from meiduo_mao.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generalte_verify_email_url,check_verify_email_token
from users.models import Address
from goods.models import SKU
from carts.utils import merge_carts_cookies_redis

# Create your views here.


logger = logging.getLogger("django")

class UserBrowseHistories(LoginRequiredJSONMixin, View):

    def post(self, request):
        # 接受参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get("sku_id")

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数sku_id错误")

        redis_conn = get_redis_connection('history')
        user = request.user
        pl = redis_conn.pipeline()

        pl.lrem(user.id, 0, sku_id)
        pl.lpush(user.id, sku_id)
        pl.ltrim(user.id, 0, 4)
        pl.execute()

        return http.JsonResponse({"code":0, "errmsg": "ok"})

    def get(self, request):
        user = request.user
        redis_conn = get_redis_connection('history')

        sku_ids = redis_conn.lrange(user.id, 0, -1)
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "default_image_url": sku.default_image.url
            })

        return http.JsonResponse({"code": 0, "errmsg": "ok"})





class UpdateTitleAddressView(LoginRequiredJSONMixin, View):

    def put(self, request, address_id):

        json_dict = json.loads(request.body.decode())
        title = json_dict.get("title")

        address = Address.objects.get(id=address_id)
        address.title = title
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class DefaultAddressView(LoginRequiredJSONMixin, View):

    def put(self, request, address_id):

        address= Address.objects.get(id=address_id)
        request.user.default_address = address
        request.user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})



class UpdateDestroyAddressView(LoginRequiredJSONMixin,View):

    def put(self, request, address_id):

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')


        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)

            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})
        address = Address.objects.get(id=address_id)

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):

        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class AddressCreateView(LoginRequiredJSONMixin,View):

    def post(self, request):
        count = request.user.addresses.count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get("receiver")
        province_id = json_dict.get("province_id")
        city_id = json_dict.get("city_id")
        district_id = json_dict.get("district_id")
        place = json_dict.get("place")
        mobile = json_dict.get("mobile")
        tel = json_dict.get("tel")
        email = json_dict.get("email")

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden("缺少必传参数")
        #
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        # #     return http.HttpResponseForbidden('参数mobile有误')
        # if tel:
        #     if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
        #         return http.HttpResponseForbidden('参数tel有误')
        # if email:
        #     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        #         return http.HttpResponseForbidden('参数email有误')

        try:
            address = Address.objects.create(
                            user = request.user,
                            title = receiver,
                            receiver = receiver,
                            province_id = province_id,
                            city_id = city_id,
                            district_id = district_id,
                            place = place,
                            mobile = mobile,
                            tel = tel,
                            email = email,
            )
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            logger.error(e)


        address_dict = {
            "id":address.id,
            "title":address.title,
            "receiver":address.receiver,
            "province":address.province.name,
            "city":address.city.name,
            "district":address.district.name,
            "place":address.place,
            "mobile":address.mobile,
            "tel":address.tel,
            "email":address.email
        }

        return http.JsonResponse({"code": "0", "errmsg": "ok", "address": address_dict})


class AddressView(LoginRequiredMixin, View):

    def get(self, request):
        login_user = request.user
        # addresses = login_user.address.filter(is_deleted=False)
        addresses = Address.objects.filter(user=login_user, is_deleted=False)

        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

        context = {
            "default_address_id": login_user.default_address_id,
            'addresses': address_dict_list
        }

        return render(request, 'user_center_site.html', context)


class VerifyEmailView(View):

    def get(self, request):
        token = request.GET.get('token')

        if not token:
            return http.HttpResponseForbidden("缺少token")

        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseForbidden("无效的token")

        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError("激活邮件失败")

        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):

    def put(self, request):

        json_data = json.loads(request.body.decode())
        email = json_data.get("email")

        if not email:
            return http.HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        verify_url = generalte_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})

class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):

        context = {
            "username":request.user.username,
            "mobile":request.user.mobile,
            "email":request.user.email,
            "email_active":request.user.email_active
        }

        return render(request, 'user_center_info.html', context=context)


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

        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        # 跳转到首页

        # response = redirect(reverse('contents:index'))

        response.set_cookie("username", username, expires=3600 * 24 * 15)

        # response = merge_carts_cookies_redis(request=request, user=user, response=response)

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



