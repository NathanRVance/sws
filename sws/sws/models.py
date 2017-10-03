from django.db import models
from django.contrib.auth.models import User

class waterInfo(models.Model):
    time_added = models.DateTimeField('date created', auto_now_add=True)
    name = models.CharField(max_length=30)
    toxicity = models.DecimalField(max_digits=5, decimal_places=2)
    address = models.CharField(max_length=80)
    image = models.CharField(max_length=50)	
    imageURL = models.CharField(max_length=80,blank=True,default="")
    fertilizer = models.CharField(max_length=8,default='U')
    filtered = models.CharField(max_length=8,default='U')
    tankAge = models.CharField(max_length=8,default='U')
    tankEmpty = models.CharField(max_length=8,default='U')
    farm = models.CharField(max_length=8,default='U')
    pet = models.CharField(max_length=8,default='No')
    school = models.CharField(max_length=20,blank=True,default="")
    
class Profile(models.Model):
	user = models.OneToOneField(User)
	address = models.CharField(max_length=150)
	filtered = models.CharField(max_length=8,default='U')
	tankAge = models.CharField(max_length=8,default='U')
	tankEmpty = models.CharField(max_length=8,default='U')
	farm = models.CharField(max_length=8,default='U')
    	pet = models.CharField(max_length=8,default='No')

class Document(models.Model):
	docfile = models.FileField()
	waterID = models.IntegerField()

