"""
URL routing for bulk operations.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Screen bulk operations
    path('screens/bulk/delete/', views.bulk_screens_delete, name='bulk-screens-delete'),
    path('screens/bulk/update/', views.bulk_screens_update, name='bulk-screens-update'),
    path('screens/bulk/activate_template/', views.bulk_screens_activate_template, name='bulk-screens-activate-template'),
    path('screens/bulk/send_command/', views.bulk_screens_send_command, name='bulk-screens-send-command'),
    
    # Template bulk operations
    path('templates/bulk/delete/', views.bulk_templates_delete, name='bulk-templates-delete'),
    path('templates/bulk/update/', views.bulk_templates_update, name='bulk-templates-update'),
    path('templates/bulk/activate/', views.bulk_templates_activate, name='bulk-templates-activate'),
    path('templates/bulk/activate_on_screens/', views.bulk_templates_activate_on_screens, name='bulk-templates-activate-on-screens'),
    
    # Content bulk operations (TODO: Implement these views)
    # path('contents/bulk/delete/', views.bulk_contents_delete, name='bulk-contents-delete'),
    # path('contents/bulk/update/', views.bulk_contents_update, name='bulk-contents-update'),
    # path('contents/bulk/download/', views.bulk_contents_download, name='bulk-contents-download'),
    # path('contents/bulk/retry/', views.bulk_contents_retry, name='bulk-contents-retry'),
    
    # Schedule bulk operations (TODO: Implement these views)
    # path('schedules/bulk/delete/', views.bulk_schedules_delete, name='bulk-schedules-delete'),
    # path('schedules/bulk/update/', views.bulk_schedules_update, name='bulk-schedules-update'),
    # path('schedules/bulk/activate/', views.bulk_schedules_activate, name='bulk-schedules-activate'),
    # path('schedules/bulk/execute/', views.bulk_schedules_execute, name='bulk-schedules-execute'),
    
    # Command bulk operations (TODO: Implement these views)
    # path('commands/bulk/delete/', views.bulk_commands_delete, name='bulk-commands-delete'),
    # path('commands/bulk/execute/', views.bulk_commands_execute, name='bulk-commands-execute'),
    # path('commands/bulk/retry/', views.bulk_commands_retry, name='bulk-commands-retry'),
]
