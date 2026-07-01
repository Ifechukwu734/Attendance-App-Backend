from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from django.utils import timezone
import uuid
from django.conf import settings
from courseManagement.models import CourseSchedule
# Create your models here.

DEPARTMENT = (
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Statistics', 'Statistics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Geology', 'Geology')
    )

class CustomUser(AbstractBaseUser, PermissionsMixin):
    LEVEL = (
        ('100 Level', '100 Level'),
        ('200 Level', '200 Level'),
        ('300 Level', '300 Level'),
        ('400 Level', '400 Level'),
    )

    email = models.EmailField(_('email address'), unique=True, db_index=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    matric_number = models.CharField(max_length=20, default='')
    level = models.CharField(max_length=12, choices=LEVEL, default='', blank=True, null=True)
    department = models.CharField(max_length=225, choices=DEPARTMENT, default='')
    device_id = models.CharField(max_length=225, default='')
    minimum_attendance = models.IntegerField(default=0)
    token_expiration_time = models.IntegerField(default=30)
    token_refresh_time = models.IntegerField(default=10)
    face_verification = models.BooleanField(default=False)
    verification_face = models.ImageField(upload_to='image/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='image/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    date_uploaded = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.is_staff is not True:
            self.matric_number = '2026/SC/' + str(uuid.uuid4().int)[:4]
        super().save(*args, **kwargs)
    



