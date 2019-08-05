try:
    # django 2.0
    from django.urls import path, include
except:
    # django 1.6
    from django.conf.urls import url as path


from . import views

urlpatterns = [
    # path('humanresources/viewprofiles/', views.list_users_by_group),
    # path('humanresources/contractproposal/approve/<int:contractproposal_id>/', views.approve_contract, name='approve_contract'),
    # path('humanresources/contractproposal/close/<int:contractproposal_id>/',   views.close_contract,   name='close_contract'),
    # path('humanresources/contractproposal/print/<int:contractproposal_id>/',   views.print_contract,   name='print_contract'),


    # path(
    #     'contractproposal/<int:proposal_id>/',
    #     views.approve_contract_proposal,
    #     name='approve_contract_proposal',
    # ),
    # path(
    #     'contractproposal/<int:proposal_id>/',
    #     views.reject_contract_proposal,
    #     name='reject_contract_proposal',
    # ),
    # path(
    #     'contractproposal/<int:proposal_id>/print/',
    #     views.print_contract_proposal,
    #     name='print_contract_proposal',
    # ),
    path('print_proposal/<int:proposal_id>/', views.print_proposal, name='print-proposal'),
]