
from django.contrib.auth.backends import ModelBackend
from django.conf import settings
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from users.models import User
from . import constants


def check_verify_email_token(token):
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = s.loads(token)
    except :
        return None
    else:
        user_id = data.get("user_id")
        email = data.get("email")
        try:
            user = User.objects.get(id=user_id,email=email)
        except:
            return None
        else:
            return user

def generalte_verify_email_url(user):

    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data={"user_id":user.id, "email":user.email}

    token = s.dumps(data).decode()

    url = settings.EMAIL_VERIFY_URL + '?token=' + token

    return url



def get_user_by_account(account):
    try:
        if re.match(r'^1[3-9][0-9]{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)

    except Exception:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        user = get_user_by_account(username)
        if user and user.check_password(password):

            return user
        else:
            return None