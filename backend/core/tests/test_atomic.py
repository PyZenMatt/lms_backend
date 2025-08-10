from django.test import TestCase, TransactionTestCase
from django.db import transaction, DatabaseError
from django.db.models import F
from django.core.exceptions import ValidationError
from django.conf import settings
from users.models import User
from courses.models import Lesson
import time
from threading import Thread
from django.test import skipIfDBFeature, tag, skipUnlessDBFeature
from unittest import skipIf, skipUnless
from django.db import connection

class AtomicTransactionTestsSQLite(TransactionTestCase):
    pass