import re

from django.shortcuts import render

# Create your views here.
# 路由 GET usernames/<username>/count/
from django.views import  View
from apps.users.models import User
from django.http import JsonResponse
class UsernameCountView(View):

    def get(self,request,username):
        # if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
        #     return JsonResponse({'code':200,'errmsg':'用户名不满足需求'})
        count=User.objects.filter(username=username).count()
        return JsonResponse({'code':200,'count':count,'errmsg':'ok'})
