# -*- coding: utf-8 -*
import abc

from django.db import models
import urllib, urllib2

# Create your models here.

STATUS_LIST = (
                ('init', 'init'),
                ('changed', 'changed'),
                ('success', 'success'),
            )

class MapperModel(models.Model):
    '''
    簡易的mapping model format

    定義簡單的 api 與 django db的簡單存取介面
    '''
    class Meta:
        abstract = True
    
    _status = models.CharField( max_length = 100,
                                choices = STATUS_LIST,
                                default = "init")
    @property
    def _api(self):
        raise NotImplementedError("uncreate this function")



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

        super(MapperModel, self).save(*args, **kwargs)
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

    def sync(self):
        '''
        資料同步處理, 可選..
        '''
        #self.__class__.clean()
        self.__class__.objects.all().delete()
        for data in self.get_all():
            data = self.unformat(data)
            mod = self.__class__.objects.create(**data)
            mod.save(status_enforce="success")

#admin list_display------------------------------------------------

    def api_helper(self):
        return '''
                <a href="{id}/insert" target="_blank">insert</a>
                <a href="{id}/update" target="_blank">update</a>
                <a href="{id}/remove" target="_blank">remove</a>
                '''.format(id=self.id)
    api_helper.allow_tags = True

#-----------------------------------------------
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
        
        

    



        



