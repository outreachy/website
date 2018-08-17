from collections import Counter
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.db.models.deletion import Collector
from django.utils.timezone import now
from home.email import send_template_mail
from home.models import Comrade, Contribution, ApplicantApproval, MentorApproval, CoordinatorApproval
import itertools
import operator

class Command(BaseCommand):
    help = 'Finds users who have the same email address'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Delete users and send email notifications (default: dry-run)',
        )

    def handle(self, *args, force, **options):
        users = User.objects.filter(email__in=
            User.objects
            .exclude(
                is_active=False,
                date_joined__lt=now() - timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS),
            )
            .values('email')
            .annotate(count=models.Count('*'))
            .filter(count__gt=1)
            .values('email')
        ).order_by('email', 'date_joined')

        deletions_by_model = Counter()
        with self.get_mail_backend(force) as connection:
            for email, group in itertools.groupby(users, key=operator.attrgetter('email')):
                try:
                    with transaction.atomic():
                        deletions_by_model += self.dedup(email, group, connection)
                        if not force:
                            raise Exception('skipped in dry-run mode')
                except Exception as e:
                    self.stdout.write(' *** {}: {}'.format(email, e))

        if deletions_by_model:
            self.stdout.write('')
            self.stdout.write('users deleted by model:')
            for model, count in deletions_by_model.most_common():
                self.stdout.write('{}: {}'.format(self.format_model(model), count))

        if not force:
            self.stdout.write('')
            self.stdout.write(' *** Nothing done in dry-run mode!')
            self.stdout.write(' *** Run again with --force to commit these changes.')

    def get_mail_backend(self, force):
        if force:
            return mail.get_connection()
        return mail.get_connection('django.core.mail.backends.console.EmailBackend', stream=self.stdout)

    def dedup(self, email, group, connection):
        accounts = [(user, self.get_cascades(user)) for user in group]
        keep = accounts

        if len(keep) > 1:
            keep = [
                (user, cascades) for user, cascades in keep
                if cascades
            ]

        if len(keep) > 1:
            minimal = set((Comrade,))
            keep = [
                (user, cascades) for user, cascades in keep
                if cascades != minimal
            ]

        if len(keep) > 1:
            important = set((Contribution, ApplicantApproval, MentorApproval, CoordinatorApproval))
            really_keep = [
                (user, cascades) for user, cascades in keep
                if not cascades.isdisjoint(important)
            ]
            if really_keep:
                keep = really_keep

        remove = dict(accounts)
        for account, cascades in keep:
            del remove[account]

        deletions_by_model = Counter()
        self.stdout.write('')

        if keep:
            self.stdout.write('keeping for {}:'.format(email))
            for account, cascades in keep:
                self.format_cascades(account, cascades)
            self.stdout.write('')

        if remove:
            self.stdout.write('deleting for {}:'.format(email))

            deletions_by_model[User] += len(remove)
            for account, cascades in remove.items():
                deletions_by_model.update(cascades)
                self.format_cascades(account, cascades)
                account.delete()
            self.stdout.write('')

            send_template_mail("home/email/dupemail.txt", {
                'accounts': [user for user, _ in accounts],
                'keeps': [user for user, _ in keep],
            }, [email], connection=connection)

        return deletions_by_model

    def get_cascades(self, user):
        c = Collector(user._state.db)
        c.collect([user])

        # figure out which models this user has data in
        existing = set(c.data.keys())
        existing.update(q.model for q in c.fast_deletes if q.exists())
        # but don't mention they have a User, that's obvious:
        existing.discard(User)
        return existing

    def format_model(self, model):
        return '{}.{}'.format(model._meta.app_label, model.__name__)

    def format_cascades(self, account, cascades):
        self.stdout.write('- {}: {}'.format(
            account.username,
            ', '.join(map(self.format_model, cascades)) or 'no models',
        ))
