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
    path('Index.html', views.home),
    path('', views.home),
    path('admin/', admin.site.urls),
    path('Signup.html', views.signup),
    path('signup/', views.signup),
    path('Rules.html', views.rules),
    path('rules/', views.rules),
    path('<int:frame>/', views.ham_redirect),
    path('HamPage.html', views.ham),
    path('ham/<int:frame>/', views.ham),
    path('me/', views.my_stuff),
    path('signout/', views.signout),
    path('statistics/', views.stats),
    # path('ham/<int:frame>/submissions.json/', views.submissions), # use cachable, get votes from userinfo.json
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
    path('images.json/<password>/', views.images),
    path('loaderio-a121e3b9103b84461b5f933652cff7c7/', views.loader_io),
    path('favicon.ico', views.favicon)
]
