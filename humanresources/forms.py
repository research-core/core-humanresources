from decimal import Decimal

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.core.exceptions import ValidationError


from crispy_forms.bootstrap import Field, InlineRadios, TabHolder, Tab

from crispy_forms.layout import Submit, Layout, Div, Fieldset, MultiField, HTML


class UserProfileForm(forms.ModelForm):
    pass


class ContractProposalForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()

        total_payouts = sum([
            Decimal(self.data[f'payment_set-{i}-amount'] or '0')
            for i in range(0, int(self.data['payment_set-TOTAL_FORMS']))
        ])

        salary = cleaned_data.get('salary', Decimal(0.00))

        if salary != total_payouts:
            msg = 'The payouts specified do not cover this value'
            raise ValidationError({'salary': msg})


class NewHireForm(ContractProposalForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-my-form'
        self.helper.form_class = 'my-form'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

        self.helper.layout = Layout(
            Fieldset(
                'Tell us your favorite stuff {{ username }}',
                'createdon',
                'start',
                'duration',
                'favorite_food',
                HTML("""
                    <p>We use notes to get better, <strong>please help us {{ username }}</strong></p>
                """),
                'notes'
            )
        )

        # self.helper.layout = Layout(
        #     MultiField(
        #         'Tell us your favorite stuff {{ username }}',
        #         Div(
        #             'like_website',
        #             'favorite_number',
        #             css_id='special-fields'
        #         ),
        #         'favorite_color',
        #         'favorite_food',
        #         'notes'
        #     )

        #    # Fieldset('Name',
        #    #          Field('person', placeholder='Your first name',
        #    #                css_class="some-class"),
        #    #          Div('last_name', title="Your last name"),),
        #    # Fieldset('Contact data', 'email', 'phone', style="color: brown;"),
        #    # InlineRadios('color'),
        #    # TabHolder(Tab('Address', 'address'),
        #    #           Tab('More Info', 'more_info')))
        # )

    # class Meta:
    #     fields = []
