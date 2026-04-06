"""
URL configuration for analytics API endpoints.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Screen analytics
    path('analytics/screens/', views.screen_statistics, name='screen-statistics'),
    path('analytics/screens/<uuid:screen_id>/', views.screen_detail, name='screen-detail'),
    
    # Command analytics
    path('analytics/commands/', views.command_statistics, name='command-statistics'),
    
    # Content analytics
    path('analytics/content/', views.content_statistics, name='content-statistics'),
    
    # Template analytics
    path('analytics/templates/', views.template_statistics, name='template-statistics'),
    
    # Activity trends
    path('analytics/activity/', views.activity_trends, name='activity-trends'),
]
