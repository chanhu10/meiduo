from django.shortcuts import render

from django.views import View
from django import http
from django.core.cache import cache

import logging


# from meiduo_mao.utils.response_code import RETCODE
from areas.models import Area

# Create your views here.

logger = logging.getLogger("django")


class AreasView(View):

    def get(self, request):
        area_id = request.GET.get("area_id")

        if not area_id:
            province_list = cache.get("province_list")

            if not province_list:
                try:
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    province_list = []
                    for province_model in province_model_list:
                        province_list.append({"id":province_model.id, "name":province_model.name})

                    province_list = cache.set("province_list", province_list, 3600)
                except Exception as e:
                    logger.error("e")
                    return http.JsonResponse({'code': 422, 'errmsg': '省份数据错误'})



            return http.JsonResponse({"code": 0, "errmsg": "ok", "province_list":province_list})

        else:
            sub_data = cache.get("sub_area_" + area_id)

            if not sub_data:

                try:
                    parent_model = Area.objects.get(id=area_id)
                    # sub_model_list = parent_model.area_set.all()
                    sub_model_list = parent_model.subs.all()
                    subs = []

                    for sub_model in sub_model_list:
                        subs.append({"id":sub_model.id, "name":sub_model.name})

                    sub_data = {"id": area_id,
                                "name": parent_model.name,
                                "subs": subs}

                    cache.set("sub_area_" + area_id, sub_data, 3600)

                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': 422, 'errmsg': '城市或区数据错误'})



            return http.JsonResponse({"code": 0, "errmsg": "OK", "sub_data": sub_data})

