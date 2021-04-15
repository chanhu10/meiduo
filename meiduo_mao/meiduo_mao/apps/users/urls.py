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

    path('addresses/create/', views.AddressCreateView.as_view(), name="addressCreate"),

    path('addresses/<int:address_id>/', views.UpdateDestroyAddressView.as_view(), name='updateaddresss'),

    path('addresses/<int:address_id>/default/', views.DefaultAddressView.as_view(), name='defaultaddresss'),

    path('addresses/<int:address_id>/title/', views.UpdateTitleAddressView.as_view(), name='updatetitle'),

    path('browse_histories/', views.UserBrowseHistories.as_view()),


]