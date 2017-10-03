from django.shortcuts import render
from django.http import HttpResponse

import requests
import os
import sys
import datetime
import subprocess

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.shortcuts import render_to_response 
from django.http import HttpResponseRedirect 
from django.contrib.auth.forms import UserCreationForm
from django.template.context_processors import csrf

from django.template import RequestContext
from django.forms import Form
from django import forms
from sws.models import waterInfo
from sws.models import Profile
from sws.forms import customRegistrationForm
from sws.forms import queryForm
from sws.forms import editForm
from django.db.models import Q
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderQuotaExceeded
from geopy.distance import vincenty
from sws.models import Document
from sws.forms import DocumentForm
from django.contrib.auth.models import User


#function that determines if an email is in the system already
def uniqueEmail(data):
    if data and User.objects.filter(email=data).exists():
        return False
    return True


#determines if an address is valid
def validAddress(addr):
    center = (41.734264,-86.148058) #Granger
    #get coordinates of address
    geolocator = GoogleV3(api_key='AIzaSyD841F7qitRh2rnKt4mxYmbdWs4DYHyyFI')

    try:
    	loc = geolocator.geocode(addr)
    except GeocoderTimedOut:
        return False
    except GeocoderQuotaExceeded:
        return True
    #see if within 50 miles
    try:
        address = (loc.latitude, loc.longitude)
    except AttributeError:
        return False
    dist = vincenty(center, address).miles
    if dist < 50: #address checks out:
        return True
    return False

#Determines if an image has a valid extension
def validImage(imgFile):
    imgName = imgFile.name
    imgList = ['.jpg','.png','.gif','.jpeg','.jif','.jfif','.tif','.tiff']
    if imgName[-4:].lower() in imgList or imgName[-5:].lower() in imgList:
        return True
    return False


#The form users see when they insert records
filter_choices = [('N','No'),('Y','Yes'),('U','Unsure')]
fertilizer_choices = [('','----'),('N','No'),('Y','Yes'),('U','Unsure')]
farm_choices = [('N','No'),('Y','Yes'),('U','Unsure')]
pet_choices = [('No','No'),('Yes','Yes')]
tankAge_choices = [('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
tankEmpty_choices = [('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
class InsertDBForm(Form):
    water_levels = forms.DecimalField(max_digits=5, required = True, label = 'Nitrate Level (ppm)')
    address = forms.CharField(max_length =80, required = True)
    fertilizer = forms.ChoiceField(required = True, choices = fertilizer_choices, label = 'Have you used fertilizer in the past week?')
    filtered = forms.ChoiceField(required = True, choices = filter_choices, label = 'Was this water sample filtered?')
    tankAge = forms.ChoiceField(required = True, choices = tankAge_choices, label = 'How old is your sceptic tank?')
    tankEmpty = forms.ChoiceField(required = True, choices = tankEmpty_choices, label = 'When did you last empty your sceptic tank?')
    farm = forms.ChoiceField(required = True, choices = farm_choices, label = 'Is there a farm within 20 miles?')
    pet = forms.ChoiceField(required = True, choices = pet_choices, label = 'Do you have any pets that you let outside?')
    docfile = forms.FileField(label = 'Add an Image', required = False)


#This handles the page where users insert records
def insert(request):
    msg = ''
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/sws/login/')
        username = request.user.get_username()
        form = InsertDBForm(request.POST)
        if form.is_valid():
            u1 = request.user
            pa = Profile.objects.get(user_id = u1.id)
            p1 = Profile.objects.filter(user_id = u1.id)
	    addr = pa.address
	    if not validAddress(form.cleaned_data['address']):
		form.cleaned_data['address'] = addr
	    if not addr == form.cleaned_data['address']:
	        p1.update(address = form.cleaned_data['address'])
		
	    try:
		float(form.cleaned_data['water_levels'])
	    except ValueError:
		msg = "Please input a number."
                return HttpResponseRedirect('/sws/insert')
            wi = waterInfo(name=username, toxicity = form.cleaned_data['water_levels'], address = form.cleaned_data['address'], filtered = form.cleaned_data['filtered'],farm = form.cleaned_data['farm'],tankAge = form.cleaned_data['tankAge'],tankEmpty = form.cleaned_data['tankEmpty'],fertilizer = form.cleaned_data['fertilizer'], pet = form.cleaned_data['pet'])
	    wi.save()
	    try:
	      newdoc = Document(waterID = wi.id, docfile = request.FILES['docfile'])
	      newdoc.save()
              waterInfos = waterInfo.objects.filter(Q(id = wi.id))
	      waterInfos.update(imageURL = newdoc.docfile.url)
	      waterInfos.update(image = request.FILES['docfile'])
	    except:
	      pass

            #fill in school based on provided addresses
            try:
              records = waterInfo.objects.filter(Q(id = wi.id))
              records.update(school = "North Point")

              records = waterInfo.objects.filter(Q(id = wi.id) & (Q(address__icontains='51640 Sandelwood') | Q(address__icontains='14869 Copper') | Q(address__icontains='51773 Sagecrest') | Q(address__icontains='51380 Coveside') | Q(address__icontains='51663 Deer Trail') | Q(address__icontains='51161 Leeward') | Q(address__icontains='13744 Kendallwood') | Q(address__icontains='51365 Amesburry') | Q(address__icontains='2907 Lexington') | Q(address__icontains='14236 Worthington') | Q(address__icontains='51896 Foxdale') | Q(address__icontains='14413 Worthington')) )

              if records:
                records.update(school = "Discovery")
            except Exception:
              pass

            try:
              email = request.user.email
              if email:
                subprocess.call(["/home/smike/sendconfirm.py",email])
            except:
              pass
            return HttpResponseRedirect('/sws/db')

    else:
        u1 = request.user
        p1 = Profile.objects.get(user_id = u1.id)
	addr = p1.address
	#Get default filtered value
	if p1.filtered == 'U':
	    filter2_choices = [('U','Unsure'),('Y','Yes'),('N','No')]
	elif p1.filtered == 'Y':
	    filter2_choices = [('Y','Yes'),('N','No'),('U','Unsure')]
	else:
	    filter2_choices = [('N','No'),('Y','Yes'),('U','Unsure')]

	#Get default pet value
	if p1.pet == 'Yes':
	    pet2_choices = [('Yes','Yes'),('No','No')]
	else:
	    pet2_choices = [('No','No'),('Yes','Yes')]

	#Get default farm value
	if p1.farm == 'U':
	    farm2_choices = [('U','Unsure'),('Y','Yes'),('N','No')]
	elif p1.farm == 'Y':
	    farm2_choices = [('Y','Yes'),('N','No'),('U','Unsure')]
	else:
	    farm2_choices = [('N','No'),('Y','Yes'),('U','Unsure')]

	#Get default tankAge value
	if p1.tankAge == '<3':
	    tankAge2_choices = [('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
	elif p1.tankAge == '3-6':
	    tankAge2_choices = [('3-6','3 to 6 years'),('<3','Less than 3 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
	elif p1.tankAge == '6-9':
	    tankAge2_choices = [('6-9','6 to 9 years'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('>9','Greater than 9 years'),('U','Unsure')]
	elif p1.tankAge == '>9':
	    tankAge2_choices = [('>9','Greater than 9 years'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('U','Unsure')]
	else:
	    tankAge2_choices = [('U','Unsure'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years')]

	#Get default tankEmpty value
	if p1.tankEmpty == '<3':
		tankEmpty2_choices = [('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	elif p1.tankEmpty == '3-6':
		tankEmpty2_choices = [('3-6','3 to 6 months'),('<3','Less than 3 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	elif p1.tankEmpty == '6-9':
		tankEmpty2_choices = [('6-9','6 to 9 months'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	elif p1.tankEmpty == '9-12':
		tankEmpty2_choices = [('9-12','9 to 12 months'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	elif p1.tankEmpty == '12-24':
		tankEmpty2_choices = [('12-24','1 to 2 years'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('>24','Greater than 2 years'),('U','Unsure')]
	elif p1.tankEmpty == '>24':
		tankEmpty2_choices = [('>24','Greater than 2 years'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('U','Unsure')]
	else:
		tankEmpty2_choices = [('U','Unsure'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years')]


        form = InsertDBForm()
	form.fields['filtered'] = forms.ChoiceField(required = True, choices = filter2_choices, label = 'Was this water sample filtered?')
    	form.fields['tankAge'] = forms.ChoiceField(required = True, choices = tankAge2_choices, label = 'How old is your sceptic tank?')
    	form.fields['tankEmpty'] = forms.ChoiceField(required = True, choices = tankEmpty2_choices, label = 'When did you last empty your sceptic tank?')
    	form.fields['farm'] = forms.ChoiceField(required = True, choices = farm2_choices, label = 'Is there a farm within 20 miles?')
	form.fields['pet'] = forms.ChoiceField(required = True, choices = pet2_choices, label = 'Do you have any pets that you let outside?')
	form.fields['address'] = forms.CharField(max_length = 80, required = True, initial = addr)
    token = {}
    token.update(csrf(request))
    token['form'] = form
    token['msg'] = msg
    return render(request, 'addDB_form.html', token)


#handles the register page
def register(request):
    if request.method == 'POST':
        #form = UserCreationForm(request.POST)
        form = customRegistrationForm(request.POST)
	msg = ""
        if form.is_valid():
	  addrST1 = form.cleaned_data['addressST1']
	  addrST2 = form.cleaned_data['addressST2']
	  addrC = form.cleaned_data['addressC']
	  addrS = form.cleaned_data['addressS']
	  addrZ = form.cleaned_data['addressZ']
	  if addrST2:
		addrST1 = addrST1 + ' ' + addrST2
	  addr = addrST1 + ', ' + addrC + ', ' + addrS + ', ' + addrZ
	  if validAddress(addr):
            if uniqueEmail(form.cleaned_data['email']):
              form.save()
              return HttpResponseRedirect('/sws/register/complete/')
            else:
              msg = "This email address is already in use."
	  else:
	    msg = "Please make sure address is input correctly and is in the Michiana Region."

            form = customRegistrationForm()
	

    else:
        form = customRegistrationForm()
	msg = " "

    token = {}
    token.update(csrf(request))
    token['form'] = form
    token['msg'] = msg
    return render_to_response('registration/registration_form.html', token)

def registration_complete(request):
    return render_to_response('registration/registration_complete.html')


def index(request):
    return render(request, 'index.html')

#handles the data page
def data(request):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'data.txt')

    locations = []
    with open(file_path) as f:
        for line in f:
            info = line.split(',')
            locations.append([float(info[0]),float(info[4]),float(info[5]),str(info[6]), float(info[7][:-1])])


    return render(request, 'data.html', {'locations':locations})

#handles the page with the database table
def db(request):

    if request.method == 'POST':
        recID = request.POST.get('id','')
        action = request.POST.get('action','')
        if action == "Delete":
	    imgURL = request.POST.get('imgURL','')
            docs = Document.objects.filter(Q(waterID = int(recID)))
	    for docToDel in docs:	
	        docToDel.docfile.delete()
	        docToDel.delete()
            waterInfos = waterInfo.objects.filter(Q(id = int(recID)))
            waterInfos.update(image = "")
            waterInfos.update(imageURL = "")

    if request.user.is_superuser:
        docs = Document.objects.all()
        waterInfos = waterInfo.objects.all().order_by("-name")
	info = {}
	count = {}
	for wInfo in waterInfos:
		if wInfo.address in info.keys():
			info[wInfo.address] = info[wInfo.address] + wInfo.toxicity
			count[wInfo.address] += 1
		else:
			count[wInfo.address] = 1
			info[wInfo.address] = wInfo.toxicity
	for key in info.keys():
		info[key] = float(info[key])/count[key]

	#Get geolocation of the datapoints	
	addrs = info.keys()
	mags = info.values()
	locations = []
	geolocator = GoogleV3('AIzaSyD841F7qitRh2rnKt4mxYmbdWs4DYHyyFI')
	for addr, mag in zip(addrs, mags):
	  try:
	    loc = geolocator.geocode(addr)
          except GeocoderTimedOut, GeocoderQuotaExceeded:
            pass
          try:
	    locations.append(loc.latitude)
            locations.append(loc.longitude)
            locations.append(mag)
          except AttributeError:
            pass
    else:
        docs = Document.objects.all()
        username = request.user.get_username()
        waterInfos = waterInfo.objects.filter(name = username).order_by('-id')
	locations = []
    recCount = waterInfos.count()
    return render(request, 'db.html', {'waterInfos': waterInfos, 'locations':locations, 'docs':docs,'recCount':recCount})

def mytest(request):
    return HttpResponse('TEST PAGE HERE')

#Handles the admin search function
def search(request):
    if not request.user.is_superuser:
    	return HttpResponseRedirect('/sws/login/')
    if request.method == 'POST':
        form = queryForm(request.POST)
        if form.is_valid():
	    formName = form.cleaned_data['name']
	    formAddr = form.cleaned_data['address']
            waterInfos = waterInfo.objects.filter(Q(name = formName) | Q(address = formAddr))
            recCount = waterInfos.count() 
            if not waterInfos:
              waterInfos = waterInfo.objects.all()

            LRange = form.cleaned_data['Lower_Range']
            URange = form.cleaned_data['Upper_Range']
            if LRange:
              waterInfos = waterInfos.filter(toxicity__gte=LRange)
            if URange:
              waterInfos = waterInfos.filter(Q(toxicity__lte=URange))

            sDate = form.cleaned_data['Start_Date']
            eDate = form.cleaned_data['End_Date']
            if sDate:
              waterInfos = waterInfos.exclude(time_added__lt=datetime.datetime.combine(sDate,datetime.time.min))
            if eDate:
              waterInfos = waterInfos.exclude(time_added__gt=datetime.datetime.combine(eDate,datetime.time.max))
	    info = {}
	    count = {}
	    for wInfo in waterInfos:
		if wInfo.address in info.keys():
			info[wInfo.address] = info[wInfo.address] + wInfo.toxicity
			count[wInfo.address] += 1
		else:
			count[wInfo.address] = 1
			info[wInfo.address] = wInfo.toxicity
	    for key in info.keys():
		info[key] = float(info[key])/count[key]

	
	    addrs = info.keys()
	    mags = info.values()
	    locations = []
	    geolocator = GoogleV3('AIzaSyD841F7qitRh2rnKt4mxYmbdWs4DYHyyFI')
	    for addr, mag in zip(addrs, mags):
	      try:
	        loc = geolocator.geocode(addr)
              except GeocoderTimedOut:
                pass
              except GeocoderQuotaExceeded:
                break
              try:
	        locations.append(loc.latitude)
                locations.append(loc.longitude)
                locations.append(mag)
              except AttributeError:
                pass

            recCount = waterInfos.count()
            return render(request, 'db.html', {'waterInfos': waterInfos.order_by('id'), 'locations':locations,'recCount':recCount})

    else:
        form = queryForm()
    token = {}
    token.update(csrf(request))
    token['form'] = form

    return render(request, 'adminQuery_form.html', token)

#handles viewing imaged
def image(request):
	if request.method == 'POST':
        	action = request.POST.get('action','')
		if action == "Add Image":
			form = DocumentForm()
        		recID = request.POST.get('id','')
		else:
			
			form = DocumentForm(request.POST, request.FILES)
			if form.is_valid():
        			recID = request.POST.get('id','')
				#if img is not valid extension then let user know
				imgName = request.FILES['docfile']
				if not validImage(imgName):
					form = DocumentForm()
        				token = {}
        				token.update(csrf(request))
        				token['form'] = form
					token['ID'] = recID
					token['msg'] = "Please use an image with a proper extension."
        				return render(request, 'imageUpload.html', token)


				newdoc = Document(waterID = recID, docfile = request.FILES['docfile'])
				newdoc.save()
          			waterInfos = waterInfo.objects.filter(Q(id = int(recID)))
          			waterInfos.update(image = request.FILES['docfile'])
				waterInfos.update(imageURL = newdoc.docfile.url)
			return HttpResponseRedirect('/sws/db')
	else:
		form = DocumentForm()
	msg = ''
        token = {}
        token.update(csrf(request))
        token['form'] = form
	token['ID'] = recID
	token['msg'] = msg
        return render(request, 'imageUpload.html', token)

#Handle the edit page
def edit(request):
    if request.method == 'POST':
        recID = request.POST.get('id','')
        action = request.POST.get('action','')
	msg = ''
        if action == "Edit":
          form = editForm()
	  msg = ''
          token = {}
          token.update(csrf(request))
	  token['ID'] = recID
	  token['msg'] = msg
          wi = waterInfo.objects.get(id = int(recID))
	  token['name'] = wi.name
	  token['address'] = wi.address
	  token['toxicity'] = wi.toxicity
	  token['filtered'] = wi.filtered
	  token['farm'] = wi.farm
	  token['fertilizer'] = wi.fertilizer
	  token['tankAge'] = wi.tankAge
	  token['tankEmpty'] = wi.tankEmpty
	  token['pet'] = wi.pet
	  token['time_added'] = wi.time_added
	  
	  if wi.filtered == 'U':
	      filter2_choices = [('U','Unsure'),('Y','Yes'),('N','No')]
	  elif wi.filtered == 'Y':
	      filter2_choices = [('Y','Yes'),('N','No'),('U','Unsure')]
	  else:
	      filter2_choices = [('N','No'),('Y','Yes'),('U','Unsure')]

		#Get default pet value
          if wi.pet == 'Yes':
            pet2_choices = [('Yes','Yes'),('No','No')]
          else:
            pet2_choices = [('No','No'),('Yes','Yes')]

	  #Get default farm value
	  if wi.farm == 'U':
	    farm2_choices = [('U','Unsure'),('Y','Yes'),('N','No')]
	  elif wi.farm == 'Y':
	    farm2_choices = [('Y','Yes'),('N','No'),('U','Unsure')]
	  else:
	    farm2_choices = [('N','No'),('Y','Yes'),('U','Unsure')]

	  #Get default fertilizer value
	  if wi.fertilizer == 'U':
	    fertilizer2_choices = [('U','Unsure'),('Y','Yes'),('N','No')]
	  elif wi.fertilizer == 'Y':
	    fertilizer2_choices = [('Y','Yes'),('N','No'),('U','Unsure')]
	  else:
	     fertilizer2_choices = [('N','No'),('Y','Yes'),('U','Unsure')]

	#Get default tankAge value
	  if wi.tankAge == '<3':
	    tankAge2_choices = [('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
	  elif wi.tankAge == '3-6':
	    tankAge2_choices = [('3-6','3 to 6 years'),('<3','Less than 3 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years'),('U','Unsure')]
	  elif wi.tankAge == '6-9':
	    tankAge2_choices = [('6-9','6 to 9 years'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('>9','Greater than 9 years'),('U','Unsure')]
	  elif wi.tankAge == '>9':
	    tankAge2_choices = [('>9','Greater than 9 years'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('U','Unsure')]
	  else:
	    tankAge2_choices = [('U','Unsure'),('<3','Less than 3 years'),('3-6','3 to 6 years'),('6-9','6 to 9 years'),('>9','Greater than 9 years')]

	#Get default tankEmpty value
	  if wi.tankEmpty == '<3':
	    tankEmpty2_choices = [('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	  elif wi.tankEmpty == '3-6':
	    tankEmpty2_choices = [('3-6','3 to 6 months'),('<3','Less than 3 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	  elif wi.tankEmpty == '6-9':
	    tankEmpty2_choices = [('6-9','6 to 9 months'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	  elif wi.tankEmpty == '9-12':
	    tankEmpty2_choices = [('9-12','9 to 12 months'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years'),('U','Unsure')]
	  elif wi.tankEmpty == '12-24':
	    tankEmpty2_choices = [('12-24','1 to 2 years'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('>24','Greater than 2 years'),('U','Unsure')]
	  elif wi.tankEmpty == '>24':
	    tankEmpty2_choices = [('>24','Greater than 2 years'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('U','Unsure')]
	  else:
	    tankEmpty2_choices = [('U','Unsure'),('<3','Less than 3 months'),('3-6','3 to 6 months'),('6-9','6 to 9 months'),('9-12','9 to 12 months'),('12-24','1 to 2 years'),('>24','Greater than 2 years')]


          form.fields['Water_levels'] = forms.DecimalField(max_digits=5,required = True, label = 'Nitrate Level (ppm)', initial = float(wi.toxicity))
          form.fields['address'] = forms.CharField(max_length = 140, required = True, initial = wi.address) 
	  form.fields['recordID'] = forms.CharField(widget=forms.HiddenInput(), initial = wi.id)
	  form.fields['filtered'] = forms.ChoiceField(required = True, choices = filter2_choices, label = 'Was this water sample filtered?')
          form.fields['tankAge'] = forms.ChoiceField(required = True, choices = tankAge2_choices, label = 'How old is your sceptic tank?')
          form.fields['tankEmpty'] = forms.ChoiceField(required = True, choices = tankEmpty2_choices, label = 'When did you last empty your sceptic tank?')
          form.fields['farm'] = forms.ChoiceField(required = True, choices = farm2_choices, label = 'Is there a farm within 20 miles?')
          form.fields['pet'] = forms.ChoiceField(required = True, choices = pet2_choices, label = 'Do you have any pets that you let outside?')
          form.fields['fertilizer'] = forms.ChoiceField(required = True, choices = fertilizer2_choices, label = 'Have you used fertilizer in the past week?')

          token['form'] = form
          return render_to_response(request, 'editForm.html', token)
        elif action == "Delete":
          docs = Document.objects.filter(Q(waterID = int(recID)))
	  for docToDel in docs:	
	    docToDel.docfile.delete()
	    docToDel.delete()
          waterInfos = waterInfo.objects.filter(Q(id = int(recID)))
          waterInfos.delete()
          return HttpResponseRedirect('/sws/db')          
        elif action == "Update":
          form = editForm(request.POST,request.FILES)
          if form.is_valid():
            level = form.cleaned_data['Water_levels']
            addr = form.cleaned_data['address']
            filt = form.cleaned_data['filtered']
            fert = form.cleaned_data['fertilizer']
            p = form.cleaned_data['pet']
            f = form.cleaned_data['farm']
            tA = form.cleaned_data['tankAge']
            tE = form.cleaned_data['tankEmpty']
            recID = form.cleaned_data['recordID']
            waterInfos = waterInfo.objects.filter(Q(id = int(recID)))
            waterInfos.update(toxicity = float(level))
            waterInfos.update(address = addr)
            waterInfos.update(filtered = filt)
            waterInfos.update(fertilizer = fert)
            waterInfos.update(pet = p)
            waterInfos.update(farm = f)
            waterInfos.update(tankAge = tA)
            waterInfos.update(tankEmpty = tE)


  	    try:
	      if request.FILES['docfile']:
                docs = Document.objects.filter(Q(waterID = int(recID)))
	        for docToDel in docs:	
	          docToDel.docfile.delete()
	          docToDel.delete()
	        newdoc = Document(waterID = int(recID), docfile = request.FILES['docfile'])
	        newdoc.save()
	        waterInfos.update(imageURL = newdoc.docfile.url)
	        waterInfos.update(image = request.FILES['docfile'])

	    except:
	      pass
            return HttpResponseRedirect('/sws/db')          

    return HttpResponseRedirect('/sws/db')

#Handle the user options page
def options(request):
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/sws/login/')
        #update location for user
	addrST1 = request.POST.get('st1','')
	if request.POST.get('st2',''):
	      addrST1 = request.POST.get('st1','') + ' ' + request.POST.get('st2','')
	newLoc = addrST1 + ', ' + request.POST.get('c','') + ', ' + request.POST.get('st','') + ', ' + request.POST.get('zip','')
	if validAddress(newLoc):
            u1 = request.user
            p1 = Profile.objects.filter(user_id = u1.id)
            if p1:
	        p1.update(address = newLoc)
            else:
                pi = Profile(user_id = u1.id, address = newLoc)
	        pi.save()
	    #change all waterInfo records here with user location
            waterInfos = waterInfo.objects.filter(Q(name = u1.username))
            waterInfos.update(address = newLoc)
            return HttpResponseRedirect('/sws/db')
	else:
            token = {}
            token.update(csrf(request))
            token['msg'] = "Please make sure address is input correctly and is in the Michiana Region."
            return render_to_response('options.html', token)
    else:
        return render(request,'options.html')

#Handle the admin users view page
def users(request):
    if not request.user.is_superuser:
      return HttpResponseRedirect('/sws/')
    if request.method == 'POST':
        recID = request.POST.get('id','')
        action = request.POST.get('action','')
        if action == "Edit":
          users = User.objects.filter(Q(id = int(recID)))
          profiles = Profile.objects.filter(Q(user_id = int(recID)))
          return render(request,'editUsers.html', {'users': users, 'profiles': profiles})
	elif action == "Delete":
	  #delete user and profile
	  u1 = User.objects.get(id = int(recID))
	  uname = u1.username
	  us = User.objects.filter(Q(id = int(recID)))
	  us.delete()
	  profs = Profile.objects.filter(Q(user_id = int(recID)))
	  profs.delete()
	  #delete all associated records
	  waterInfos = waterInfo.objects.filter(Q(name = uname))
	  waterInfos.delete()
	  return HttpResponseRedirect('/sws/users')
	elif action == "Update":
	  #Update users and profiles
	  nname = request.POST.get('name','')
	  nemail = request.POST.get('email','')
	  naddr = request.POST.get('address','')
	  u1 = User.objects.get(id = int(recID))
	  uname = u1.username
	  uemail = u1.email
	  users = User.objects.filter(Q(id = int(recID)))
	  users.update(username = nname)
	  users.update(email = nemail)
	  profs = Profile.objects.filter(Q(user_id = int(recID)))
	  profs.update(address = naddr)
	  #Change all associated records
	  waterInfos = waterInfo.objects.filter(Q(name = uname))
          waterInfos.update(name = nname, address = naddr)
	  return HttpResponseRedirect('/sws/users')
	elif action == "Promote":
	  check = request.POST.get('check','')
	  u1 = User.objects.get(id = int(recID))
	  uname = u1.username
	  if uname == check:
		u1.is_superuser = True
		u1.save()
	  return HttpResponseRedirect('/sws/users')
	
    else:
      profs = Profile.objects.all()
      recCount = profs.count()
      return render(request, 'users.html', {'profs': profs, 'recCount':recCount})

#404 page
def handler404(request):
    response = render(request, '404.html', {})
    response.status_code = 404
    return response

#simple tutorial page
def tutorial(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/sws/login/')
    return render(request, 'tutorial.html')

#simple prizes page
def prizes(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/sws/login/')
    return render(request, 'prizes.html')
