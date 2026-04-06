"""
URL routing for content validation endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('content-validation/validate/', views.validate_content, name='validate-content'),
    path('content-validation/bulk/', views.validate_bulk_content, name='validate-bulk-content'),
]
