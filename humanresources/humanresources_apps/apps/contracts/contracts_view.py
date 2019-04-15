from .contracts_form import ContractEditFormWidget


class Contract(ContractEditFormWidget):

    def __init__(self, obj=None):
        super().__init__(title='Test', pk=obj)