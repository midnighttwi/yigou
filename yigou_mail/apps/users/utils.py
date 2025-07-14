from django.db.models.expressions import result
from django.http import JsonResponse
from django.views import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from apps.users.models import User
from yigou_mail import settings

# 加密
def generic_email_verify_token(user_id):

    s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600*24)
    # 加密
    token=s.dumps({'user_id':user_id})
    return  token

# 解密
def check_verify_token(token):

    s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600*24)
    # 解密
    try:
        result=s.loads(token)
    except Exception as e:
        return None

    # 获取数据
    return result.get('user_id')

