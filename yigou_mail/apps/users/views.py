import json
import re

from django.contrib.auth import logout
from django.shortcuts import render

# Create your views here.
# 路由 GET usernames/<username>/count/
from django.views import  View
from apps.users.models import User, Address
from django.http import JsonResponse

from apps.users.utils import check_verify_token
from utils.views import LoginRequiredJSONMixin

class UsernameCountView(View):

    def get(self,request,username):
        # if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
        #     return JsonResponse({'code':200,'errmsg':'用户名不满足需求'})
        count=User.objects.filter(username=username).count()
        return JsonResponse({'code':0,'count':count,'errmsg':'ok'})


class RegisterView(View):

    def post(self,request):

        body_bytes=request.body
        body_str=body_bytes.decode()
        body_dict=json.load(body_str)

        username=body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile=body_dict.get('mobile')
        allow=body_dict.get('allow')

        if not all([username,password,password2,mobile,allow]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})

        #用户名
        if not re.match(r'^[a-zA-Z0-9]{8,20}$',username):
            return JsonResponse({'code':400,'errmsg':'用户名不满足规则'})
        # 密码

        # 用户密码加密
        user=User.objects.create_user(username=username,password=password,mobile=mobile)
        # 系统（Django）为我们提供了 状态保持的方法
        from django.contrib.auth import login
        login(request, user)

        return JsonResponse({'code':0,'errmsg':'ok'})


class LoginView(View):

    def post(self,request):

        # 接收数据
        data=json.loads(request.body.decode())
        username=data.get('username')
        password=data.get('password')
        remembered=data.get('remembered')

        # 验证
        if not all([username,password]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})

        # 判断用户填写的是手机号还是用户名，改变查询字段
        if re.match(r'^[a-zA-Z0-9]{8,20}$',username):
            User.USERNAME_FIELD='mobile'
        else:
            User.USERNAME_FIELD='username'

        # 用户名和密码
        # 如果通过，返回USer信息，如果不对，则返回None
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is not None:
            return JsonResponse({'code':400,'errmsg':'账户或密码错误'})

        # 判断是否记住登录
        if remembered is not None:
            #记住登录状态（n时间内免登录）
            request.session.set_expiry(None)# 默认两周
        else:
            request.session.set_expiry(0)

        # 返回响应
        reponse=JsonResponse({'code': 0, 'errmsg': 'ok'})
        reponse.set_cookie('username',username,max_age=3600)
        return reponse


class LogoutView(View):

    def delete(self,request):
        logout(request)
        return JsonResponse({'code': 0, 'errmsg': 'ok'})




class CenterView(LoginRequiredJSONMixin,View):

    def get(self,request):

        info_data={
            'username':request.user.username,
            'email':request.user.email,
            'mobile':request.user.mobile,
            'email_activated':request.user.email_activate,
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok','info_data':info_data})



class EmailView(LoginRequiredJSONMixin,View):

    def put(self,request):

        data=json.loads(request.body.decode())
        email=data.get('email')

        #保存邮箱
        user=request.user
        user.email=email
        user.save()
        # 发送邮件
        from django.core.mail import send_mail

        subject = '易购商城激活邮件'
        # message,      邮件内容
        message = ""
        # from_email,   发件人
        from_email = '易购商城<urstjshsuxj@163.com>'
        # recipient_list, 收件人列表
        recipient_list = ['urstjshsuxj@163.com']

        # 邮件的内容如果是 html 这个时候使用 html_message
        from apps.users.utils import generic_email_verify_token
        token = generic_email_verify_token(request.user.id)

        verify_url = "http://www.meiduo.site:8080/success_verify_email.html?token=%s" % token
        # 4.2 组织我们的激活邮件
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用易购商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

        # 邮件异步发送
        from celery_tasks.email.tasks import celery_send_email
        celery_send_email.delay(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message
        )

        return JsonResponse({'code': 0, 'errmsg': 'ok'})

#
class EmailVerifyView(View):

    def put(self,request):
        params=request.GET
        token=params.get('token')

        if token is None:
            return JsonResponse({'code':400,'errmsg':'参数缺失'})
        # 获取user_id
        user_id=check_verify_token(token)
        if user_id is None:
            return JsonResponse({'code':400,'errmsg':'<UNK>'})

        user=User.objects.get(id=user_id)
        user.email_active=True
        user.save()

        return JsonResponse({'code':200,'errmsg':'ok'})


class AddressCreateView(LoginRequiredJSONMixin,View):

    def post(self,request):

        # 接收数据
        data=json.loads(request.body.decode())

        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        user = request.user

        # 数据入库
        address = Address.objects.create(
            user=user,
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

        # 转化为字典
        address_dict = {
            'id': address.id,
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

        # 4.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})

# 查询地址
class AddressView(LoginRequiredJSONMixin,View):

    def get(self,request):
        # 查询指定数据
        user=request.user

        addresses=Address.objects.filter(user=user,is_deleted=False)

        #将对象数据转换为字典数据
        address_list=[]
        for address in addresses:
            address_list.append({
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
            })

        #返回响应
        return JsonResponse({'code':0,'errmsg':'ok','addresses':address_list})
