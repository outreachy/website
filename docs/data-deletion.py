# This documents how to delete an object along with everything that has
# a non-null foreign key reference to it, plus all version history for
# all the deleted objects.

# This is not quite executable as-is, but has a few pseudo-coded bits to
# be filled in depending on what exactly you're trying to do with it.

from django.db.models.deletion import Collector
import reversion
from reversion.models import Version, Revision

# Assume we've loaded an object from the database:
obj = ...

# The normal way to delete `obj` would be to call `obj.delete()`.
# Internally that uses Collector (a sadly undocumented interface), which
# we can use directly to check what's going to happen before actually
# modifying the database.
c = Collector(obj._state.db)
c.collect([obj])

# After calling c.collect,
# c.data contains some objects the delete cascades to; keys are by model
# c.fast_deletes contains QuerySets for the remaining objects the delete cascades to
# c.field_updates contains objects with foreign keys to set to NULL

# So we can find all the objects that should be deleted:
fast_delete_pks = [(q.model, list(q.values_list('pk', flat=True))) for q in c.fast_deletes]
slow_delete_pks = [(model, [o.pk for o in objects]) for model, objects in c.data.items()]
delete_pks = [(model, pks) for model, pks in fast_delete_pks + slow_delete_pks if pks]

# We can refuse to delete certain models. (Insert appropriate policies
# and error reporting mechanisms for however you're using this.)
for model, pks in delete_pks:
    if model == InternSelection:
        raise AssertionError("tried to delete a selected intern")
    if model.__module__ in ('wagtail.users.models', 'django.contrib.admin.models'):
        raise AssertionError("don't delete staff-generated data")

# At this point, we could present a summary for the user of what's about
# to be deleted and prompt them to make sure they actually want to
# delete all of it. There are probably internal-use models we shouldn't
# tell them about though, such as anything in the
# 'django.contrib.auth.models' module.
render(request, '...', { 'collector': c })

# For all the objects the Collector has decided to delete, find their
# version history if any.
versions = []
for model, pks in delete_pks:
    # If this model is not registered for version control, it shouldn't
    # have any versions for us to delete.
    if not reversion.is_registered(model): continue
    # Find the primary key of every Revision and Version that touches
    # the objects we're deleting.
    versions.extend(Version.objects.get_for_model(model).filter(object_id__in=pks).values_list('revision', 'pk'))

# Now we know all the versions we want to delete, and what revision they
# come from. We want to delete the revisions as well. But it's possible
# for a revision to touch many objects at once, and deleting a revision
# deletes all of its versions, and we don't want to delete versions for
# objects that we aren't deleting. So we need to check if the revisions
# exactly cover the versions we've picked out.
revisions = set(revision for revision, version in versions)
full_revisions = set(Revision.objects.filter(pk__in=revisions).order_by().values_list('pk', 'version'))
if full_revisions.difference(versions):
    # Whoops, there's some Revision where we're only deleting some of
    # the Versions in it. Simplest option is to refuse to delete
    # anything in this case.
    raise AssertionError("didn't implement partial deletion of revisions")

# Assuming that we really do want to delete these revisions in their
# entirety, add them to the collection.
c.collect(Revision.objects.filter(pk__in=revisions).order_by())

# Finally, call `c.delete()` to actually delete everything.




import reversion
from reversion.models import Version, Revision
from home import models

# Delete revisions for all objects of particular types:
version_query = Version.objects.none()
for model in (models.ApplicantApproval, models.BarriersToParticipation, models.ApplicantGenderIdentity, models.ApplicantRaceEthnicityInformation, models.SchoolInformation):
    version_query |= Version.objects.get_for_model(model)

# Delete all selected versions.
version_query.order_by().delete()

# If any revisions no longer have any object versions inside them, delete those
# too. This may also delete revisions that were already empty beforehand, but
# those revisions didn't have any useful information in them anyway, because
# they were empty.
Revision.objects.exclude(pk__in=Version.objects.values('revision')).order_by().delete()
