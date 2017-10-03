"""sws URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
import views

urlpatterns = [
    url(r'^sws/$', views.index, name='index'),
    url(r'^sws/db', views.db, name='db'),
    url(r'^sws/data', views.data, name='data'),
    url(r'^sws/mytest', views.mytest, name='mytest'),
    url(r'^sws/insert', views.insert, name='insert'),
    url(r'^sws/search', views.search, name='search'),
    url(r'^sws/address', views.options, name='options'),
    url(r'^sws/users', views.users, name='users'),
    url(r'^sws/prizes', views.prizes, name='prizes'),
    url(r'^sws/edit', views.edit, name='edit'),
    url(r'^sws/tutorial', views.tutorial, name='tutorial'),
    url(r'^sws/login/$', auth_views.login, name='login'),
    url(r'^sws/logout/$', auth_views.logout, {'next_page': '/sws'}, name='logout'),
    # Registration URLs
    url(r'^sws/accounts/register/$', views.register, name='register'),
    url(r'^sws/accounts/register/complete/$', views.registration_complete, name='registration_complete'),
    url(r'^sws/register/$', views.register, name='register'),
    url(r'^sws/register/complete/$', views.registration_complete, name='registration_complete'),
    url(r'^sws/$', views.image, name='image'),
    url(r'^sws/image/$', views.image, name='image'),
]
