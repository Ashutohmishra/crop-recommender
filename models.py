from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete = models.CASCADE)
    phone = models.CharField(max_length=20)


    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prediction")

    N = models.FloatField()
    P = models.FloatField()
    K = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()

    predicted_label = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta :
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} -> {self.predicted_lable}"
        


# profiles/models.py

from django.db import models
from django.contrib.auth.models import User
import random
import string

class FarmerProfile(models.Model):
    COUNTRY_CHOICES = [
        ('india', 'India'),
        ('bangladesh', 'Bangladesh'),
        ('pakistan', 'Pakistan'),
        ('nepal', 'Nepal'),
        ('sri_lanka', 'Sri Lanka'),
        ('myanmar', 'Myanmar'),
        ('thailand', 'Thailand'),
        ('vietnam', 'Vietnam'),
        ('indonesia', 'Indonesia'),
        ('philippines', 'Philippines'),
        ('malaysia', 'Malaysia'),
        ('china', 'China'),
        ('japan', 'Japan'),
        ('south_korea', 'South Korea'),
    ]

    CROP_CHOICES = [
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('maize', 'Maize/Corn'),
        ('sugarcane', 'Sugarcane'),
        ('cotton', 'Cotton'),
        ('soybean', 'Soybean'),
        ('groundnut', 'Groundnut'),
        ('pulses', 'Pulses'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('spices', 'Spices'),
        ('tea', 'Tea'),
        ('coffee', 'Coffee'),
        ('jute', 'Jute'),
        ('tobacco', 'Tobacco'),
        ('other', 'Other'),
    ]

    HELP_CHOICES = [
        ('financial', 'Financial Assistance'),
        ('seeds', 'Quality Seeds'),
        ('fertilizers', 'Fertilizers & Pesticides'),
        ('equipment', 'Farming Equipment'),
        ('irrigation', 'Irrigation Support'),
        ('training', 'Training & Education'),
        ('market', 'Market Access'),
        ('insurance', 'Crop Insurance'),
        ('loan', 'Agricultural Loan'),
        ('weather', 'Weather Information'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    phone_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    # India specific fields
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    pm_kisan_registered = models.BooleanField(default=False)
    pm_kisan_id = models.CharField(max_length=20, blank=True, null=True)
    
    # Common fields
    current_crops = models.JSONField(default=list, blank=True)
    land_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    land_unit = models.CharField(max_length=20, default='acres')
    help_needed = models.JSONField(default=list, blank=True)
    help_description = models.TextField(blank=True, null=True)
    
    # Government verification
    govt_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    address = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    village = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.country}"

    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.save()
        return self.verification_code

    def verify_phone(self, code):
        if self.verification_code == code:
            self.phone_verified = True
            self.verification_code = None
            self.save()
            return True
        return False

    @property
    def is_indian(self):
        return self.country == 'india'

    def get_crops_display(self):
        crop_dict = dict(self.CROP_CHOICES)
        return [crop_dict.get(crop, crop) for crop in self.current_crops]

    def get_help_display(self):
        help_dict = dict(self.HELP_CHOICES)
        return [help_dict.get(h, h) for h in self.help_needed]
# models.py  (in your app - e.g. recommender/models.py)
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MessageToGovernment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    photo = models.ImageField(upload_to='government_photos/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    reply = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Msg to Govt from {self.user.username} - {self.created_at.date()}"

class MessageToAgriculture(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    photo = models.ImageField(upload_to='agri_photos/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    reply = models.TextField(blank=True, null=True)          # agriculture officer reply

    def __str__(self):
        return f"Msg to Agri from {self.user.username} - {self.created_at.date()}"