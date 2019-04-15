from django.http import HttpResponse
from humanresources.models import ContractProposal


def print_proposal(request, proposal_id):

    queryset = ContractProposal.objects.filter(pk=proposal_id)

    if not queryset.has_print_permissions(request.user):
        return HttpResponse('No permissions')

    proposal = ContractProposal.objects.get(pk=proposal_id)
    return proposal.generate_pdf_view(request)
