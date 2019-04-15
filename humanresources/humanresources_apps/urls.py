from . import views
from django.urls import path

urlpatterns = [
    path('print_proposal/<int:proposal_id>/', views.print_proposal, name='print-proposal'),
]