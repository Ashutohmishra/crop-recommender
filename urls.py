from django.urls import path
from . import views
from .views import change_password_view

app_name = "recommender"   # good practice for namespacing

urlpatterns = [

    # Home
    path('', views.home, name="home"),

    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Crop Prediction
    path('predict/', views.predict_view, name='predict'),

    # Prediction History
    path('user-history/', views.user_history_view, name='user_history'),

# FIXED DELETE URL
path('delete-prediction/<int:id>/', views.user_delete_prediction, name='user_delete_prediction'),

    # Farmer Profile
    path('profile/', views.profile_form, name='profile_form'),
    path('profile/preview/<int:profile_id>/', views.profile_preview, name='profile_preview'),

    # Phone Verification
    path('profile/send-code/', views.send_verification_code, name='send_verification_code'),
    path('profile/verify-phone/', views.verify_phone, name='verify_phone'),

    # Country Dynamic Fields
    path('profile/country-fields/', views.get_country_fields, name='country_fields'),
    path('change_password/',change_password_view , name = 'change_password'),

    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('users/', views.user_view, name='user_view'),
  path('users/', views.user_management, name='user_management'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('send-message/govt/', views.send_message_govt, name='send_message_govt'),
    path('send-message/agri/', views.send_message_agri, name='send_message_agri'),
  path('prediction-analysis/<str:crop>/', views.prediction_analysis_view, name='prediction_analysis'),
    # ... other paths
]