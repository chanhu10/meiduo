from django.urls import path
from . import views

urlpatterns = [

    path('image_codes/<str:uuid>/', views.ImageCodeView.as_view(), name="ImageCodeView"),
    path('register/sms_codes/<int:mobile>/', views.SMSCodeView.as_view()),

]