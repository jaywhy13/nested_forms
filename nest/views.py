from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext

from crispy_forms.helper import FormHelper

from nest.forms import (BuildingFormSet, 
	BlockForm, 
	InlineFormset,
	nested_formset_factory
	)
from nest.models import Block, Building, Tenant

def home(request):
	blocks = Block.objects.all()
	# Declare the form and the formset
	form = BlockForm(request.POST or None)
	formset = InlineFormset(request.POST or None)
	helper = FormHelper()
	helper.form_tag = False

	if form.is_valid():
		if formset.is_valid():
			print("The format is VALID")
			obj = form.save()
			formset.instance = obj
			formset.save()
		else:
			message = "The formset is invalid"
	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))


