from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper

from nest.forms import (BuildingFormSet, 
	BlockForm, 
	BuildingForm,
	TenantForm,
	FurnitureForm,
	InlineFormset,
	nested_formset_factory
	)
from nest.models import Block, Building, Tenant, Furniture

model_maps = {
	"block" : Block,
	"building" : Building,
	"tenant" : Tenant,
	"furniture" : Furniture
}

form_maps = {
	"block" : BlockForm,
	"building" : BuildingForm,
	"tenant" : TenantForm,
	"furniture" : FurnitureForm
}

def home(request):
	blocks = Block.objects.all()
	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))

def new_block(request):
	form = BlockForm(request.POST or None)
	if form.is_valid():
		form.save()
		return redirect("/")
	return render_to_response("new_form.html", locals(), 
		context_instance=RequestContext(request))

def edit_model(request, model, pk):
	blocks = Block.objects.all()
	if model not in model_maps:
		raise Http404("Huh?!?!?")
	model_class = model_maps.get(model)
	form_class = form_maps.get(model)
	obj = get_object_or_404(model_class, pk=pk)
	form = form_class(request.POST or None, instance=obj)
	if form.is_bound and form.is_valid():
		form.save()
		return redirect(reverse("edit-model", kwargs=dict(model=model, pk=pk)))

	return render_to_response("form.html", locals(), 
		context_instance=RequestContext(request))

def delete_model(request, model, pk):
	if model not in model_maps:
		raise Http404("Huh?!?!?")
	model_class = model_maps.get(model)
	obj = get_object_or_404(model_class, pk=pk)
	obj.delete()
	return redirect("/")

def testing(request):
	return render_to_response("testing.html")
	