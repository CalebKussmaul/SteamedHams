"""SteamdHams2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from SteamedHamsFinal import views

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),
    path('signup/', views.signup),
    path('signout/', views.signout),
    path('<int:frame>/', views.ham_redirect),
    path('ham/<int:frame>/', views.ham),
    path('ham/<int:frame>/submissions.json/', views.submissions),
    path('ham/<int:frame>/cachable_submissions.json/', views.cachable_submissions),
    path('ham/<int:frame>/upvote/', views.upvote),
    path('ham/<int:frame>/downvote/', views.downvote),
    path('ham/<int:frame>/report/', views.report),
    path('ham/<int:frame>/submit/', views.submit),
    path('ham/<int:frame>/delete/', views.delete),
    path('userinfo.json/', views.userinfo),
    path('download/', views.download),
    path('render/', views.rendervideo),
    path('composite/', views.composite),
    path('statistics/', views.stats),
    path('rules/', views.rules),
    # path('favicon.ico/', views.favicon)
]
