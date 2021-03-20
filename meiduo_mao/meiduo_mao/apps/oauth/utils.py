from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings

from . import constants


def check_access_token(access_token_openid):

    s = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    try:
        data = s.loads(access_token_openid)
    except BadData:
        return None
    else:

        return data.get("openid")


def generate_access_token(openid):

    s = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    data = {"openid":openid}
    token = s.dumps(data)

    return token.decode()


