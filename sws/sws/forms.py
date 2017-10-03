from django import forms
from django.forms import Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from sws.models import Profile
from sws.models import waterInfo
from django.forms import SelectDateWidget
import datetime

filter_choices = [('','---'),('N','No'),('Y','Yes'),('U','Unsure')]
pet_choices = [('','---'),('No','No'),('Yes','Yes')]
tankAge_choices = [('','---'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
tankEmpty_choices = [('','---'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
farm_choices = [('','---'),('N','No'),('Y','Yes'),('U','Unsure')]
fertilizer_choices = [('N','No'),('Y','Yes'),('U','Unsure')]
class DocumentForm(forms.Form):
	docfile = forms.FileField(
		label = 'Select a file',
	)

class customRegistrationForm(UserCreationForm):
	addressST1 = forms.CharField(max_length=40, required = True, label = 'Street address 1')
	addressST2 = forms.CharField(max_length=40, required = False, label = 'Street address 2 (Optional)')
	addressC = forms.CharField(max_length=20, required = True, label = 'City')
	addressS = forms.CharField(max_length=20, required = True, label = 'State')
	addressZ = forms.CharField(max_length=10, required = True, label = 'ZIP')
	filtered = forms.ChoiceField(required = True, choices = filter_choices, label = 'Is your water source filtered?')
	tankAge = forms.ChoiceField(required = True, choices = tankAge_choices, label = 'How old is your sceptic tank?')
	tankEmpty = forms.ChoiceField(required = True, choices = tankEmpty_choices, label = 'When was the last time you emptied your sceptic tank?')
	farm = forms.ChoiceField(required = True, choices = farm_choices, label = 'Is there a farm within 20 miles?')
	pet = forms.ChoiceField(required = True, choices = pet_choices, label = 'Do you have any pets that you let outside?')

	class Meta:
		model = User
		fields = ('username', 'password1', 'password2', 'email')

	def save(self,commit = True):
		user1 = super(customRegistrationForm, self).save(commit = False)

		if commit:
			user1.save()
			p1 = Profile(user=user1,address="")
	  		p1.address = self.cleaned_data['addressST1'] + ', ' + self.cleaned_data['addressC'] + ', ' + self.cleaned_data['addressS'] + ', ' + self.cleaned_data['addressZ']
			if self.cleaned_data['addressST2']:
	  			p1.address = self.cleaned_data['addressST1'] + ' ' + self.cleaned_data['addressST2'] + ', ' + self.cleaned_data['addressC'] + ', ' + self.cleaned_data['addressS'] + ', ' + self.cleaned_data['addressZ']
			p1.filtered = self.cleaned_data['filtered']
			p1.tankAge = self.cleaned_data['tankAge']
			p1.tankEmpty = self.cleaned_data['tankEmpty']
			p1.farm = self.cleaned_data['farm']
			p1.pet = self.cleaned_data['pet']
			p1.save()
		return user1

class editForm(Form):
	Water_levels = forms.DecimalField(max_digits=5,required = True, label = 'Nitrate Level (ppm)')
        address = forms.CharField(max_length = 140, required = True) 
	filtered = forms.ChoiceField(required = True, choices = filter_choices, label = 'Is your water source filtered?')
	tankAge = forms.ChoiceField(required = True, choices = tankAge_choices, label = 'How old is your sceptic tank?')
	tankEmpty = forms.ChoiceField(required = True, choices = tankEmpty_choices, label = 'When was the last time you emptied your sceptic tank?')
	farm = forms.ChoiceField(required = True, choices = farm_choices, label = 'Is there a farm within 20 miles?')
	pet = forms.ChoiceField(required = True, choices = pet_choices, label = 'Do you have any pets that you let outside?')
	fertilizer = forms.ChoiceField(required = True, choices = fertilizer_choices, label = 'Have you used fertilizer in the past week?')
        docfile = forms.FileField(label = 'Add an Image', required = False)
	recordID = forms.CharField(widget=forms.HiddenInput())

class queryForm(Form):
	
	objs = waterInfo.objects.all().order_by("-name")
	seen = set()
	keep = []
	for o in objs:
		if o.name not in seen:
			keep.append(o)
			seen.add(o.name)

	nameChoice = []
	addrChoice = []
	nameChoice.append(("---",""))
	addrChoice.append(("---",""))
	for k in keep:
		nameChoice.append((k.name,k.name))
		addrChoice.append((k.address,k.address))
	name = forms.ChoiceField(choices=nameChoice)
	address = forms.ChoiceField(choices=addrChoice)

	Lower_Range = forms.DecimalField(min_value=0.0, required = False)
	Upper_Range = forms.DecimalField(min_value=0.0, required = False)

	Start_Date = forms.DateField(widget=SelectDateWidget(years=[2016,2017,2018]),required = False)
	End_Date = forms.DateField(widget=SelectDateWidget(years=[2016,2017,2018]),initial=datetime.date.today)

	def __init__(self, *args, **kwargs):
		super(queryForm, self).__init__(*args, **kwargs)
		allChoices = [("---","")]
		nameChoices = [ (c.name, c.name) for c in waterInfo.objects.all()]
		allChoices.extend(list(set(nameChoices)))
		self.fields['name'].choices =  allChoices
		allChoices = [("---","")]
		addrChoices = [ (c.address, c.address) for c in waterInfo.objects.all()]
		allChoices.extend(list(set(addrChoices)))
		self.fields['address'].choices = allChoices
	
