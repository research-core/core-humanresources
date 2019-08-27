from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.exceptions import FieldError
from django.core.mail import send_mail as django_send_mail
from django.template.loader import render_to_string


def create_proposal(contract, motive, responsible):
    """
    Create a Proposal based on given Contract.
    The motive can be:
        - update: renegotiate active contract terms
        - renew: only available when a contract is about to expire
    """

    assert motive in ('update', 'renewal')

    Proposal = apps.get_model('humanresources', 'ContractProposal')
    Payment = apps.get_model('humanresources', 'Payment')

    new_proposal = Proposal(
        motive=motive,
        # contract=contract,
        responsible=responsible,
        person=contract.person,
        supervisor=contract.supervisor,
        start=contract.start,
        months_duration=contract.months_duration,
        days_duration=contract.days_duration,
        salary=contract.salary,
        scientificdesc=contract.description,
        fellowship_type=contract.fellowship_type,
        position=contract.position,
    )
    new_proposal.save()

    for payout in contract.payout_set.all():
        payment = Payment(
            contractproposal=new_proposal,
            project=payout.project,
            amount=payout.amount,
        )
        payment.save()

    return new_proposal


def send_mail(subject, recipient_list, message_context={}):
    """A wrapper around Django `send_mail` method.

    Generates both plain text and HTML content.

    The templates must be in `templates/emails/`.
    The message subject determines the template used. For example, for a
    subject 'Automatic Warning' the following templates are required:

    - `templates/emails/automatic_warning.txt`
    - `templates/emails/automatic_warning.html`
    """

    if not all([subject, recipient_list]):
        # TODO Log this in the future
        # No recipients, no message, then no need to prepare the email
        print("WARNING: Mail not sent")
        return

    template_dir = 'emails'
    template_filename = subject.lower().replace(' ', '_')

    html_message = render_to_string(
        template_name=f'{template_dir}/{template_filename}.html',
        context=message_context,
    )
    message = render_to_string(
        template_name=f'{template_dir}/{template_filename}.txt',
        context=message_context,
    )

    django_send_mail(
        subject=f'[CORE] {subject}',
        message=message,
        from_email=None,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=html_message,
    )
