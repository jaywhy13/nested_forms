from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'nest.views.home', name='home'),
	url(r'^edit/(?P<model>\w+)/(?P<pk>\d+)/$', 'nest.views.edit_model', name='edit-model'),
	url(r'^delete/(?P<model>\w+)/(?P<pk>\d+)/$', 'nest.views.delete_model', name='delete-model'),
    url(r'^new-block/$', 'nest.views.new_block', name='new-block'),
    url(r'^testing/$', 'nest.views.testing', name='testing'),

    # url(r'^nested_forms/', include('nested_forms.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
