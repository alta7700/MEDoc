from django.urls import path
from . import views

urlpatterns = [
    path('about-us/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('registration/', views.RegisterView.as_view(), name='registration'),
    path('', views.index, name='home')
]

