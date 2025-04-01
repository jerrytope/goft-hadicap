from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
     path('submit-score/', submit_score, name='submit_score'),
    path('dashboard/', dashboard, name='dashboard'),
     path('leaderboard/', leaderboard, name='leaderboard'),
     path("upload/", upload_players, name="upload_players"),
]
