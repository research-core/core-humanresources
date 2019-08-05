from .privateinfo import PrivateInfoFormWidget


class ProfilePrivateInfoFormWidget(PrivateInfoFormWidget):

    POPULATE_PARENT = False

    def get_buttons_row(self):
        return []
