from django.conf.urls import patterns, include, url
from football.home import Home
from football.team import TeamProfile
from football.maker import MatchMaker
from football.overview import WeekOverview
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', Home.as_view(), name='home'),
	url(r'^team/(?P<team>\d+)/$', TeamProfile.as_view()),
	url(r'^maker/$', MatchMaker.as_view(), name='maker'),
	url(r'^overview/$', WeekOverview.as_view(), name='overview'),
	url(r'^admin/', include(admin.site.urls)),
	(r'^pics/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)
