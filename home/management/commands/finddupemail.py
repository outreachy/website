from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.deletion import Collector
import itertools
import operator

class Command(BaseCommand):
    help = 'Finds users who have the same email address'

    def handle(self, *args, **options):
        users = User.objects.filter(email__in=
            User.objects.values('email')
            .annotate(count=models.Count('*'))
            .filter(count__gt=1)
            .values('email')
        ).order_by('email')

        for email, group in itertools.groupby(users, key=operator.attrgetter('email')):
            self.stdout.write(email)
            for user in group:
                c = Collector(users.db)
                c.collect([user])

                # figure out which models this user has data in
                existing = set(c.data.keys())
                existing.update(q.model for q in c.fast_deletes if q.exists())
                # but don't mention they have a User, that's obvious:
                existing.discard(User)

                self.stdout.write('- {} has: {}'.format(user.username, ', '.join('{}.{}'.format(model._meta.app_label, model.__name__) for model in existing)))
