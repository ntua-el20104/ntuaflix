from . import views
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
    path("admin/upload/titlebasics", views.upload_title_basics, name='upload title basics'),
    path("admin/upload/titlebasics", views.upload_title_basics, name='upload title basics'),

    path("admin/upload/namebasics", views.upload_names, name='upload name basics'),
    path("admin/upload/titleakas", views.upload_akas, name='upload title akas'),
    path("admin/upload/titlecrew", views.upload_crews, name='upload title crews'),
    path("admin/upload/titleprincipals", views.upload_principals, name='upload title principals'),
    path("admin/upload/titleepisode", views.upload_episodes, name='upload title episode'),
    path("admin/upload/titleratings",views.upload_ratings, name='upload ratings'),
    path("admin/healthcheck/html", views.healthcheck, name='health check'),
    path("admin/healthcheck", views.healthcheck_json, name='health check_json'),

    path("admin/resetall", views.resetall_json, name='reset all json'),
    path("admin/resetall/html", views.resetall, name='reset all'),
    
    path("searchtitle/html", views.search_titles, name='search_title'),
    path("searchtitle", views.search_titles_json, name='search_title_json'),

    path("searchname/html",views.search_names, name='search_name'),
    path("searchname",views.search_names_json, name='search_name_json'),
    
    path("bygenre/html",views.bygenre, name='bygenre_html'),
    path("bygenre",views.bygenre_json, name="bygenre_json"),

    path('application/x-www-form-urlencoded', views.user_endpoint_view, name='user-endpoint'),
    
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]