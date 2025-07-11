from django.db import models

# Create your models here.
# 自己定义模型
# 密码要加密，要实现登录密码验证
# class User(models.Model):
#     username=models.CharField(max_length=20,unique=True)
#     password=models.CharField(max_length=20)
#     mobile=models.CharField(max_length=11,unique=True)

# django自带的用户模型
# 有密码加密 和密码验证
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    mobile=models.CharField(max_length=11,unique=True)

    class Meta:
        db_table='tb_users'
        verbose_name='用户管理'
        verbose_name_plural=verbose_name