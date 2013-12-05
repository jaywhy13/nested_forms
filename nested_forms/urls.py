from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'nest.views.home', name='home'),
	url(r'^edit/(?P<pk>\d+)$', 'nest.views.edit_block', name='edit-block'),
	url(r'^delete/(?P<pk>\d+)$', 'nest.views.delete_block', name='delete-block'),
    # url(r'^nested_forms/', include('nested_forms.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
