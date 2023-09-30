from django.urls import path
from . import views
from .views import get_story


urlpatterns = [
    path('', views.index, name="index"),
    path('code_match', views.checkCodeMatch, name="code_match"),
    path('login/', views.login, name="login"),
    path('register/', views.register, name="register"),
    path('logout/', views.logout_user, name="logout"),
    path('profile/', views.profile_user, name="profile_user"),


    path('create_story/', views.create_story, name="create_story"),
    path('read_story/<int:id>/', views.read_story, name="read_story"),
    path('api/', get_story, name='get_story')
    # path('request_story/', views.request_story)
]
