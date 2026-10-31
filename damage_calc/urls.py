from django.contrib import admin
from django.urls import path
from calculator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.team_builder, name='home'),
    path('builder/', views.team_builder, name='team_builder'),
    path('teams/', views.team_manager, name='team_manager'),
    path('save-team/', views.save_team, name='save_team'),
    path('delete-team/<int:team_id>/', views.delete_team, name='delete_team'),
    path('delete-member/<int:member_id>/', views.delete_member, name='delete_member'),
    path('battle/<int:team_id>/', views.battle_simulator, name='battle_simulator'),
    path('simulate-turn/', views.simulate_turn, name='simulate_turn'),
]