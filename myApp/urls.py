from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("login",views.login, name="login"),
    path("logout",views.logout,name="logout"),

    path("name", views.names, name="name"),
    path('name/<str:nconst>', views.name_details_json, name='name details json'),
    path('name/<str:nconst>/html', views.name_details, name ='name details html'),

    path("title", views.titles, name="titles"),
    path("title/<str:tconst>",views.title_details_json, name="title details json"),
    path("title/<str:tconst>/html",views.title_details, name="title details html"),

   
    path("upload",views.upload, name="upload"),
    path("upload/titlebasics", views.upload_title_basics, name='upload title basics'),
    path("upload/namebasics", views.upload_names, name='upload name basics'),
    path("upload/titleakas", views.upload_akas, name='upload title akas'),
    path("upload/titlecrew", views.upload_crews, name='upload title crews'),
    path("upload/titleprincipals", views.upload_principals, name='upload title principals'),
    path("upload/titleepisode", views.upload_episodes, name='upload title episode'),
    path("upload/titleratings",views.upload_ratings, name='upload ratings'),
    path("healthcheck", views.healthcheck, name='health check'),
    path("resetall", views.resetall, name='reset all'),
    
    path("searchtitle/html", views.search_titles, name='search_title'),
    path("searchtitle", views.search_titles_json, name='search_title_json'),

    path("searchname/html",views.search_names, name='search_name'),
    path("searchname",views.search_names_json, name='search_name_json'),
    
    path("bygenre/html",views.bygenre, name='bygenre_html'),
    path("bygenre",views.bygenre_json, name="bygenre_json"),

    path('application/x-www-form-urlencoded', views.user_endpoint_view, name='user-endpoint')
    
]