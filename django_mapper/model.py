# -*- coding: utf-8 -*
__all__ = ['HttpMapperModel', 'MapperModel']
import abc

from django.db import models
import urllib, urllib2

# Create your models here.

STATUS_LIST = (
                ('init', 'init'),
                ('changed', 'changed'),
                ('success', 'success'),
            )

class BaseMapperModel(models.Model):
    '''
    簡易的mapping model format

    定義簡單的 api 與 django db的簡單存取介面
    '''
    class Meta:
        abstract = True

    _base_exclude = ('_status',)
    _exclude = tuple()
    _status = models.CharField( max_length = 100,
                                choices = STATUS_LIST,
                                default = "init")

    def save(self, status_enforce=None, *args, **kwargs):
        '''
        定義 model 寫入時動作
        status = unsend & changed 則 不動作
        status = sended 則 修改狀態為 changed
        '''
        if self._status == "success":
            self._status = "changed"

        if status_enforce:
            self._status = status_enforce

        super(BaseMapperModel, self).save(*args, **kwargs)
    
#-----------------------------------------------

    def format(self):
        '''
        model 轉 api data 格式
        '''
        raise NotImplementedError("uncreate this function")

    def unformat(self):
        '''
        api 資料 轉model 格式
        '''
        raise NotImplementedError("uncreate this function")

    def get_all(self):
        '''
        從api server 擷取全部
        '''
        raise NotImplementedError("uncreate this function")


#admin list_display------------------------------------------------

    def api_helper(self):
        return '''
                <a href="{id}/insert" target="_blank">insert</a>
                <a href="{id}/update" target="_blank">update</a>
                <a href="{id}/remove" target="_blank">remove</a>
                '''.format(id=self.id)
    api_helper.allow_tags = True

#-----------------------------------------------
    def insert(self):
        raise NotImplementedError("uncreate this function")

    def update(self):
        raise NotImplementedError("uncreate this function")

    def remove(self):
        raise NotImplementedError("uncreate this function")



class HttpMapperModel(BaseMapperModel):
    '''
    http api mapper model
    '''

    @property
    def _api(self):
        raise NotImplementedError("uncreate this function")


    def send(self, api, data={}):
        data.update(self._api.BASE_PARAMS)
        data = urllib.urlencode(data)
        req = urllib2.Request(
                    url = api,
                    data = data,
                )
        return urllib2.urlopen(req).read()


    def update(self):
        '''
        更新當前model 對應到的資料
        '''
        assert self._status == "changed", 'not changed'

        update_api = self._api.UPDATE

        data = self.format()
        
        result = self.send(update_api, data)

        self.save(status_enforce = "success")

        return result

        

    def insert(self):
        '''
        將當前model 資料 新增到 api server
        '''
        assert self._status == "init", "always inserted"

        insert_api = self._api.INSERT

        data = self.format()
        
        result = self.send(insert_api, data)

        data = self.unformat(result)

        self.__dict__.update(data)
        self.save(status_enforce = "success")

        return result

    
    def remove(self):
        '''
        刪除當前model 對應到的資料
        '''
        assert self._status != "init", "not inserted"

        remove_api = self._api.REMOVE

        data = self.format()
        
        result = self.send(remove_api, data)
        
        self.save(status_enforce = "init") 

        return result
        
        
class MapperModel(BaseMapperModel):
    class Meta:
        abstract = True

    
    @property
    def _key(self):
        return self.pk

    @property
    def _model(self):
        raise NotImplementedError("uncreate this function")

    def __init__(self, *args, **kwargs):
        self._exclude += (self._key, ) + self._base_exclude
        return super(MapperModel, self).__init__(*args, **kwargs)

    def get_all(self):
        return self._model.objects.all()

    def insert(self):
        assert self._status == "init", "always inserted"
        data = self.format()
        result = self._model(**data)
        result.save()
        data = self.unformat(result)

        self.__dict__.update(data)
        self.save(status_enforce = "success")
        return self

    def update(self):
        assert self._status == "changed", 'not changed'


        data = self.format()
        
        result = self._model(**data).save()

        self.save(status_enforce = "success")

        return result
    
    def remove(self):
        assert self._status != "init", "not inserted"


        data = self.format()
        
        result = self._model.objects.get(pk=data.__dict__.get(self._key))
        result.delete()
        
        self.save(status_enforce = "init") 

        return result

    def get_mapper(self):
        assert self._status!="init", "status is not {}".format(self._status)
        return self._model.objects.get(pk=self.__dict__.get(self._key))

    @classmethod
    def sync(cls, pk):
        mod = cls.objects.get(**{cls._key:pk})
        if mod:
            return mod
        org = cls._model.objects.get(pk=pk)
        data = cls().unformat(org)
        mod = cls.objects.create(**data)
        mod.save(status_enforce="success")
        return mod


