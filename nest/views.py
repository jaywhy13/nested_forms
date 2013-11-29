from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext

from nest.forms import (BuildingFormSet, 
	BlockForm, 
	nested_formset_factory
	)
from nest.models import Block, Building, Tenant

def home(request):
	blocks = Block.objects.all()
	nested_form = nested_formset_factory(Block, Building, Tenant)(request.POST or None)
	formset = BuildingFormSet()
	form = BlockForm(request.POST or None)
	if form.is_valid():
		form.save()
	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))


