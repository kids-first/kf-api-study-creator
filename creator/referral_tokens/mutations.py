import graphene
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils import timezone
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.studies.models import Study, Membership
from creator.referral_tokens.models import ReferralToken
from creator.events.models import Event


def get_studies(input):
    """
    Convert a list of id of studies into a list of Study objects
    """
    studies_input = input.get("studies", [])
    study_ids = [from_global_id(s)[1] for s in studies_input]
    studies = Study.objects.filter(kf_id__in=study_ids).all()
    if len(studies) < len(studies_input):
        raise GraphQLError("Study does not exist.")

    return studies


def get_groups(input):
    """
    Convert a list of id of groups into a list of Group objects
    """
    groups_input = input.get("groups", [])
    group_ids = [from_global_id(g)[1] for g in groups_input]
    groups = Group.objects.filter(id__in=group_ids).all()
    if len(groups) < len(groups_input):
        raise GraphQLError("Group does not exist.")

    return groups


class ReferralTokenInput(graphene.InputObjectType):
    email = graphene.String(
        required=True, description="The email address to send the referral to"
    )

    studies = graphene.List(
        graphene.ID,
        description="A list of studies that the user will be added to upon"
        " exchange of the token",
        required=False,
    )

    groups = graphene.List(
        graphene.ID,
        required=False,
        description="The permission group the user will be given after"
        " exchanging the token",
    )


class CreateReferralTokenMutation(graphene.Mutation):
    class Arguments:
        input = ReferralTokenInput(
            required=True, description="Attributes for the new referral token"
        )

    referral_token = graphene.Field(
        "creator.referral_tokens.schema.ReferralTokenNode"
    )

    def mutate(self, info, input):
        """
        Create a new referral token
        - Checks for existing tokens who has same email and is valid to avoid
          duplicated invitations being sent
        - Create a new referral token if there is no existing ones and return
          the referral token object
        """

        user = info.context.user

        if not user.has_perm("referral_tokens.add_referraltoken"):
            raise GraphQLError("Not allowed")

        studies = get_studies(input)
        groups = get_groups(input)

        existing_token = ReferralToken.objects.filter(
            email=input["email"],
            created_at__lte=timezone.now(),
            created_at__gte=timezone.now()
            - timedelta(days=settings.REFERRAL_TOKEN_EXPIRATION_DAYS),
        ).count()

        if existing_token > 0:
            raise GraphQLError("Invite already sent, awaiting user response")

        referral_token = ReferralToken(email=input["email"], created_by=user)
        referral_token.full_clean()
        referral_token.save()
        referral_token.studies.set(studies)
        referral_token.groups.set(groups)
        referral_token.save()

        # Send email
        if referral_token.created_by.username:
            subject = (
                f"{referral_token.created_by.display_name} invited you to "
                "join the Kids First Data Tracker"
            )
        else:
            subject = "Invitation to join the Kids First Data Tracker"
        ctx = {"studies": studies, "url": referral_token.invite_url}
        send_mail(
            subject=subject,
            recipient_list=[referral_token.email],
            from_email=None,
            fail_silently=False,
            message=render_to_string(template_name="invite.txt", context=ctx),
            html_message=render_to_string(
                template_name="invite.html", context=ctx
            ),
        )

        # Log an event
        if user:
            message = (
                f"{user.display_name} invited {referral_token.email} to"
                f" {len(input['studies'])} studies"
            )
        else:
            message = (
                f"{referral_token.email} was invited to"
                f" {len(input['studies'])} studies"
            )

        event = Event(description=message, event_type="RT_CRE")
        if not user._state.adding:
            event.user = user
        event.save()

        return CreateReferralTokenMutation(referral_token=referral_token)


class ExchangeReferralTokenMutation(graphene.Mutation):
    class Arguments:
        token = graphene.ID(
            required=True, description="The id of the referral token"
        )

    user = graphene.Field("creator.users.schema.UserNode")
    referral_token = graphene.Field(
        "creator.referral_tokens.schema.ReferralTokenNode"
    )

    def mutate(self, info, token):
        """
        Exchange a referral token
        - Check if the token exists and is still valid
        - If valid, add studies and groups to user object and return the user
          object with success message
        """

        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Not allowed")

        try:
            _, uuid = from_global_id(token)
            referral_token = ReferralToken.objects.get(uuid=uuid)
        except (ReferralToken.DoesNotExist, ValidationError):
            raise GraphQLError("Referral token does not exist.")

        if not referral_token.is_valid:
            raise GraphQLError("Referral token is not valid.")

        # Add user as a collaborator to each study
        for study in referral_token.studies.all():
            membership, created = Membership.objects.get_or_create(
                study=study,
                collaborator=user,
                invited_by=referral_token.created_by,
            )

        user.groups.add(*referral_token.groups.all())
        referral_token.claimed = True
        referral_token.claimed_by = user
        referral_token.save()

        # Log an event
        message = (
            f"{user.display_name} claimed token for "
            "{len(referral_token.studies)} studies."
        )

        event = Event(description=message, event_type="RT_CLA")
        if not user._state.adding:
            event.user = user
        event.save()

        return ExchangeReferralTokenMutation(
            referral_token=referral_token, user=user
        )


class Mutation(graphene.ObjectType):
    create_referral_token = CreateReferralTokenMutation.Field(
        description="Create a referral token"
    )
    exchange_referral_token = ExchangeReferralTokenMutation.Field(
        description="Exchange a referral token"
    )
