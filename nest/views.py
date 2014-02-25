from django.shortcuts import render_to_response, get_object_or_404, redirect
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
	form = BlockForm(request.POST or None, instance=Block.objects.all()[0])

	if form.is_valid():
		obj = form.save()
		return redirect("home")

	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))

def edit_block(request, pk):
	blocks = Block.objects.all()
	block = get_object_or_404(Block, pk=pk)
	form = BlockForm(instance=block)	
	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))

def delete_block(request, pk):
	block = get_object_or_404(Block, pk=pk)
	block.delete()
	return redirect("/")

def testing(request):
	return render_to_response("testing.html")
	