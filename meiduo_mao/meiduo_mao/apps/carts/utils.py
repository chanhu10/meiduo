
import pickle, base64

from django_redis import get_redis_connection

def merge_carts_cookies_redis(request, user, response):
    """
    合并购物网车
    :return:
    """
    cart_str = request.COOKIES.get('carts')
    # 判断cookies中的购物车数据是否存在
    if not cart_str:
        return "不考虑"


    cookie_cart_str_bytes = cart_str.encode()
    cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
    cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)


    new_cart_dict = {}
    new_selected_add = []
    new_selected_rem = []
    for sku_id, cookies_dict in cookie_cart_dict.items():

        new_cart_dict[sku_id]={
            'count':cookies_dict['count']
        }
        if cookies_dict['selected']:
            new_selected_add.append(sku_id)

    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()

    pl.hmset('carts_%s'%user.id, new_cart_dict)
    if new_selected_add:
        pl.sadd('selected_%s'%user.id, *new_selected_add)
    if new_selected_rem:
        pl.srem('selected_%s'%user.id, *new_selected_rem)

    pl.execute()

    response.delete_cookie('carts')

    return response


