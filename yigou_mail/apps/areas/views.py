from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.core.cache import cache
from apps.areas.models import Area


# Create your views here.
# 针对不经常发生变化的数据可以缓存下来，减少数据库查询次数
# 比如（省市区、店铺之类的）
# 不经常发生变化：针对不同业务具体而定
# django缓存工具
class AreaView(View):

    def get(self,request):

        # 先查询缓存，如果有则直接返回,没有则查询数据库并保存到缓存中
        province_list=cache.get('province')
        if province_list is None:

            #省份
            provinces=Area.objects.filter(parent_id=None)

            # 将QuerySet对象转换为字典(JSONResponse自动转换字典)
            province_list=[]
            for province in provinces:
                province_list.append({
                    'id':province.id,
                    'name':province.name,
                })

            # 第一次查询缓存数据
            cache.set('province',province_list,24*3600)

        return JsonResponse({'code':0,'errmsg':'ok','province_list':province_list})

class SubAreaView(View):

    def get(self,request,id):
        # 先获取缓存数据
        data_list = cache.get('city:%s' % id)

        if data_list is None:
            # 获取省份id、市的id,查询信息
            # Area.objects.filter(parent_id=id)
            # Area.objects.filter(parent=id)

            up_level = Area.objects.get(id=id)  #
            down_level = up_level.subs.all()  #
            # 将对象转换为字典数据
            data_list = []
            for item in down_level:
                data_list.append({
                    'id': item.id,
                    'name': item.name
                })

            # 缓存数据
            cache.set('city:%s' % id, data_list, 24 * 3600)

        return JsonResponse({'code':0,'errmsg':'ok','sub_data':{'subs':data_list}})