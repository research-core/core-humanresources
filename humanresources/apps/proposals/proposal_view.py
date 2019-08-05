from .proposals_form import EditContractProposalFormWidget


class Proposal(EditContractProposalFormWidget):

    UID = 'view-proposal'

    def __init__(self, obj=None):
        super().__init__(pk=obj)