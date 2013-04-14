from django.contrib import admin
from django.conf import settings
from django.conf.urls import patterns, url
from django.template.response import TemplateResponse

def base_view(view):

    def base(self, request, *args):
        try:
            return view(self, request, *args)
        except Exception, e:
            return TemplateResponse(request, self._error_template , {"msg":e.message })

    return base

class MapperAdmin(admin.ModelAdmin):
    
    _error_template  = "mapping/error.html"
    _insert_template = "mapping/insert.html"
    _update_template = "mapping/update.html"
    _remove_template = "mapping/remove.html"
    change_form_template = "mapping/mapping_change_from.html"

    def __init__(self, *args):
        self.readonly_fields += ("_status", )
        super(MapperAdmin, self).__init__(*args)

    def get_urls(self):
        '''
            add page action for admin change api server
        '''
        urls = super(MapperAdmin, self).get_urls()

        my_urls = patterns('',
            url(r'^(\d+)/update/$', self.update_view),
            url(r'^(\d+)/insert/$', self.insert_view),
            url(r'^(\d+)/remove/$', self.remove_view),
        )
        return my_urls + urls 
    

    @base_view
    def update_view(self, request, pk):
        result = self.model.objects.get(pk=pk).update()

        return TemplateResponse(request, self._update_template, result)

    @base_view
    def insert_view(self, request, pk):
        result = self.model.objects.get(pk=pk).insert()

        return TemplateResponse(request, self._insert_template, result)

    @base_view
    def remove_view(self, request, pk):
        result = self.model.objects.get(pk=pk).remove()

        return TemplateResponse(request, self._remove_template, result)
       

