from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.Register.as_view(), name='register'),

    path('register/usernames/<str:username>/count/', views.UsernameCountView.as_view()),

    path('login/', views.LoginView.as_view(), name='login'),

    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('info/', views.UserInfoView.as_view(), name='info'),

    path('emails/', views.EmailView.as_view()),

    path('emails/verification/', views.VerifyEmailView.as_view()),

    path('address/', views.AddressView.as_view(), name='address'),


]