from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View




# Create your views here.
class ImageCodeView(View):

    def get(self, request,uuid):

        from libs.captcha.captcha import captcha
        # text是内容 image是图片二进制
        text,image=captcha.captcha.generate_captcha()

        # 链接redis
        from django_redis import get_redis_connection
        redis_cli=get_redis_connection('code')

        # 设置有效期
        redis_cli.setex(uuid,100,text)

        return HttpResponse(image,content_type='image/jpeg')

class SmsCodeView(View):

    def get(self,request,mobile):

        image_code=request.GET.get('image_code')
        uuid=request.GET.get('image_code_id')

        if not all([image_code,uuid]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})

        # 验证图片验证码
        # 连接redis
        from django_redis import get_redis_connection
        redis_cli=get_redis_connection('code')

        redis_image_code=redis_cli.get(uuid)
        if redis_image_code is None:
            return JsonResponse({'code':400,'errmsg':'图片验证码已过期'})
        #对比
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':400,'errmsg':'图片验证码错误'})

        # 提取发送短信的标记，看看有没有
        send_flag=redis_cli.get('send_flag_%s'%mobile)

        if send_flag is not None:
            return JsonResponse({'code':400,'errmsg':'不要频繁发送短信'})

        # 生成短信验证码
        from  random import randint
        sms_code= '%06d'%randint(0,999999)

        # 管道 3步
        # 新建一个管道
        pipeline=redis_cli.pipeline()
        # 管道收集指令
        # 保存短信验证码
        pipeline.setex(mobile, 300, sms_code)
        # 添加一个发送标记.有效期 60秒 内容是什么都可以
        pipeline.setex('send_flag_%s' % mobile, 60, 1)
        # 管道执行指令
        pipeline.execute()

        from celery_tasks.sms.tasks import celery_send_sms_code
        # delay 的参数 等同于 任务（函数）的参数
        celery_send_sms_code.delay(mobile,sms_code)

        # 7. 返回响应
        return JsonResponse({'code':0,'errmsg':'ok'})

