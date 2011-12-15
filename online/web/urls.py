from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       (r'^$', 'localangle.views.index'),
                       (r'^news/(?P<state>[^/]+)/$', 'localangle.views.news'),
                       (r'^news/(?P<state>[^/]+)/(?P<city>[^/]+)/$', 'localangle.views.news'),
    # Example:
    # (r'^web/', include('web.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
