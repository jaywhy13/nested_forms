import inspect
import re

from django.forms import *
from django.forms.models import (
	modelformset_factory,
	inlineformset_factory,
	BaseInlineFormSet
)
from django import forms
from django.utils import html

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button, Layout

from nest.models import Building, Block, Tenant, Furniture


def to_underscore_case(name):
	""" Converts title case to underscore case
	"""
	s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
	return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()



class NestedModelForm(ModelForm):

	def __init__(self, *args, **kwargs):

		if args and args[0]:
			args = list(args)
			data = args[0]
			# HACK: Go through all the management forms and make sure that
			# the number initial forms matches the number of IDS that are available
			data = data.copy()
			keys = data.keys()
			for key in keys:
				if key.endswith("-INITIAL_FORMS"):
					num_initial = int(data[key])
					prefix = key[:-14]
					actual_initial = len([_key for _key in keys if re.match("%s\-\d+\-id" % prefix, _key) and data[_key] != ''])
					if num_initial != actual_initial:
						data[key] = actual_initial
			args[0] = data
		formset = kwargs.pop("formset", None)
		self.formset_initial = kwargs.pop("formset_initial", {})
		child_form = kwargs.pop("child_form", None)
		child_actions_form = kwargs.pop("child_actions_form", None)
		super(NestedModelForm, self).__init__(*args, **kwargs)
		if not self.prefix:
			self.prefix = ""
		self.setup_nested_form(child_form, child_actions_form, formset=formset)

	def add_form(self, **kwargs):
		""" Adds a form to the list of forms and initializes it with the kwargs supplied
		"""
		total_forms = self.inline_form.total_form_count()
		form = self.inline_form._construct_form(total_forms, **kwargs)
		form.fields["DELETE"].widget = HiddenInput()
		self.inline_form.forms.append(form)

		self.inline_form.data = self.inline_form.data.copy()
		total_count_name = '%s-%s' % (self.inline_form.management_form.prefix, "TOTAL_FORMS")
		if total_count_name in self.inline_form.management_form.initial:
			self.inline_form.management_form.initial[total_count_name] = self.inline_form.management_form.initial["TOTAL_FORMS"] + 1
		return form

	def process_initial(self):
		""" Looks at the initial and sees if we need to add any forms. If we 
			have something in the initial and it doesn't have an ID yet,
			it won't show up in the forms. So we need to add a form for it.
		"""
		print("Processing initial: %s for %s" % (self.formset_initial, self.__class__.__name__))
		inline_form = self.inline_form
		prefix = inline_form.prefix
		total_form_count_name = "%s-TOTAL_FORMS" % prefix
		if total_form_count_name in self.formset_initial:
			total_form_count = int(self.formset_initial[total_form_count_name])
			undeleted_form_count = 0
			for i in range(total_form_count):
				form_prefix = "%s-%s" % (prefix, i)
				id_name = "%s-id" % form_prefix
				delete_key = "%s-DELETE" % form_prefix
				delete_value = self.formset_initial.get(delete_key, "off")
				if delete_value == "on":
					continue
				undeleted_form_count += 1
				#print("This form has prefix: %s" % form_prefix)
				#print("Looking for an id with key: %s" % id_name)

				form_initial = {}
				for key, value in self.formset_initial.iteritems():
					if key.startswith(form_prefix):
						key_without_prefix = key[len(form_prefix) + 1:]
						form_initial[key_without_prefix] = value
				#print("This form has initial: %s" % form_initial)
				pk = self.formset_initial.get(id_name, "")
				if not pk:
					# We need to add a form for this..
					print("Creating form: %s" % form_prefix)
					form = self.add_form()
				else:
					print("Will update initial for: %s" % form_prefix)
					form = inline_form.forms[i]
				# If this form is a nested form, we need to process the initial for it as well
				if issubclass(form.__class__, NestedModelForm):
					print("Updating nested form %s with initial: %s" % (form.__class__.__name__, form_initial))
					form.formset_initial.update(self.formset_initial)
					form.process_initial()
				else:
					print("Updating %s with initial: %s" % (form.__class__.__name__, form_initial))
					form.initial.update(form_initial)
			self.formset_initial[total_form_count_name] = undeleted_form_count
		else:
			print("Could not find %s in the initial: %s" % (total_form_count_name, self.formset_initial))


	def get_uc_form_name(self):
		""" Returns the underscore cased version
		"""
		return to_underscore_case(self.get_form_name())

	def is_valid(self):
		valid = super(NestedModelForm, self).is_valid()
		# Check if the inline form is valid
		if self.inline_form:
			valid &= self.inline_form.is_valid()
		return valid

	def save(self, commit=True, save_formset=True):
		result = super(NestedModelForm, self).save(commit=commit)

		if self.inline_form:
			if save_formset:
				self.inline_form.save(commit=commit)
		return result

	def setup_nested_form(self, child_form, child_actions_form=None, formset=None):
		""" This function declares a property "inline_form" that contains
			the inline formset (generated using the inlineformset_factory).
			Additionally, if the user had supplied a "cihld_actions_form" 
			that is also setup under the "inline_actions_form" property.
			This is done so that the nested_form template tag can 
			search for both these properties and create the necessary template
			Crispy Nodes so that Django can render them normally. 
			Finally, key thing to note here is that this method also
			ensures that data is passed to the child form so that it 
			renders the appropriate data is the form is already bound.
			TODO: Think about nesting a form within a InlineFormset
			TODO: Removal of forms... the delete button not showing up
			TODO: SUbmission of data, the submit buttons are going to appear some
			where else basically. 
			TODO: Add the radio button logic
		"""
		self.parent_model = self._meta.model # this form 
		self.child_model = child_form._meta.model if child_form else None
		self.child_form = child_form
		self.child_actions_form = child_actions_form
		self.inline_prefix = None
		if not formset:
			formset = ManangeFormCachedBaseInlineFormset
		if child_form:
			InlineFormset = inlineformset_factory(self.parent_model, 
				self.child_model, extra=0,
				formset=formset,
				form=child_form)
			prefix_separator = "-" if self.prefix else ""
			self.inline_form = InlineFormset(
				instance=self.instance,
				data=self.data if self.is_bound else None,
				prefix = "%s%s%s" % (
					self.prefix,
					prefix_separator,
					InlineFormset.get_default_prefix()
					)
				)
			self.inline_form.actions_form = child_actions_form
			self.inline_prefix = InlineFormset.get_default_prefix()
			self.process_initial()
		else:
			self.inline_form = None
			self.inline_actions_form = None

	@staticmethod
	def get_add_child_js(child_form, parent_form):
		""" Returns the JS call necessary to add a child to this form of type
			"child_form" to a given form. Also need to specify the parent_form.
		"""
		if inspect.isclass(child_form):
			child_form = child_form()
		if inspect.isclass(parent_form):
			parent_form = parent_form()
		return "click: addChildForm"
		# % (child_form.get_form_name(), parent_form.inline_prefix)

	@staticmethod
	def get_delete_child_js():
		""" Returns the JS call necessary to delete a child form from this form
		"""
		return "deleteChild(this)"

class BuildingActionsForm(Form):

	def __init__(self, *args, **kwargs):
		super(BuildingActionsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		# Make sure that the form tag is set to False
		self.helper.form_tag = False
		# Add a button to add a building
		self.helper.add_input(Button("add_building", "Add Building",
			data_bind="%s" % NestedModelForm.get_add_child_js(BuildingForm,
				BlockForm)))

class BlockForm(NestedModelForm):
	def __init__(self, *args, **kwargs):
		# Set the child form
		kwargs["child_form"] = BuildingForm
		kwargs["child_actions_form"] = BuildingActionsForm
		#kwargs["formset"] = SpecialBuildingFormset
		super(BlockForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag = False
		self.helper.add_input(Submit("submit", "Create Block"))

	class Meta:
		model = Block

class BuildingForm(ModelForm):

	def __init__(self, *args, **kwargs):
		#kwargs["child_form"] = TenantForm
		#kwargs["child_actions_form"] = TenantActionsForm
		super(BuildingForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'
		self.helper.add_input(Submit("submit", "Create Building"))
		self.helper.layout = Layout("id", "name", "DELETE","street_name",
				Button("delete_button", "Remove Building", onclick="deleteChild(this);")
			)

	class Meta:
		model = Building		
		exclude = ["block"]

class TenantActionsForm(Form):

	def __init__(self, *args, **kwargs):
		super(TenantActionsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		# Make sure that the form tag is set to False
		self.helper.form_tag = False
		# Add a button to add a building
		self.helper.add_input(Button("add_tenant", "Add Tenant",
			data_bind="%s" % NestedModelForm.get_add_child_js(TenantForm,
				BuildingForm)))


class TenantForm(NestedModelForm):

	def __init__(self, *args, **kwargs):
		kwargs["child_form"] = FurnitureForm
		super(TenantForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'
		self.helper.add_input(Submit("submit", "Create Tenant"))

	class Meta:
		model = Tenant
		exclude = ["building"]

class FurnitureForm(ModelForm):
	class Meta:
		model = Furniture

BuildingFormSet = modelformset_factory(Building, form=BuildingForm, extra=0)
TenantFormSet = modelformset_factory(Tenant, form=TenantForm)
InlineFormset = inlineformset_factory(Block, Building, extra=0)

class BaseNestedFormset(BaseInlineFormSet):

	def __init__(self, *args, **kwargs):
		super(BaseNestedFormset, self).__init__(*args, **kwargs)
		for form in self.forms:
			form.fields["DELETE"].widget = HiddenInput()

	def add_fields(self, form, index):
		super(BaseNestedFormset, self).add_fields(form, index)

	def is_valid(self):
		""" Check if the other nested forms are valid as well
		"""
		result = super(BaseNestedFormset, self).is_valid()
		for form in self.forms:
			result = result and form.inline_form.is_valid() if hasattr(form, "inline_form") else result
			#print("  Is %s valid? %s" % (form.__class__.__name__, result))
		return result

	def save(self, commit=True):
		result = super(BaseNestedFormset, self).save(commit=commit)
		# for form in self.forms:
		# 	if hasattr(form, "inline_form"):			
		# 		form.inline_form.save(commit=commit)
		cleaned_datas = self.cleaned_data
		for i in range(len(self.forms)):
			form = self.forms[i]
			cleaned_data = cleaned_datas[i]
			save_formset = not cleaned_data.get("DELETE")
			if hasattr(form, "inline_form"):
				form.inline_form.save(commit=commit, save_formset=save_formset)
				#print("Saving form: %s" % form.__class__.__name__)
		return result

def nested_formset_factory(parent_model, child_model, grandchild_model=None):
	""" Create a formset factory that handles a 3-level relationship
	"""
	parent_child = inlineformset_factory(
		parent_model,
		child_model,
		formset=BaseNestedFormset,
		extra=1
		)

	parent_child.nested_formset_class = inlineformset_factory(
		child_model,
		grandchild_model,
		formset=BaseNestedFormset,
		extra=1
		)
	return parent_child

class ManangeFormCachedBaseInlineFormset(BaseNestedFormset):

	@property
	def management_form(self):
		if not hasattr(self, "_management_form"):
			self._management_form = super(ManangeFormCachedBaseInlineFormset, self).management_form
		return self._management_form

	def save(self, commit=True, save_formset=True):
		if save_formset:
			super(ManangeFormCachedBaseInlineFormset, self).save(commit=commit)


class SpecialBuildingFormset(ManangeFormCachedBaseInlineFormset):

	def get_queryset(self):
		qs = super(SpecialBuildingFormset, self).get_queryset()
		return qs.filter(name__startswith="A")
