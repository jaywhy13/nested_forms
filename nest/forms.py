from django.forms import ModelForm
from django.forms.models import (
	modelformset_factory,
	inlineformset_factory,
	BaseInlineFormSet
)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from nest.models import Building, Block, Tenant

class BlockForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(BlockForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag = False

	class Meta:
		model = Block

class BuildingForm(ModelForm):

	def __init__(self, *args, **kwargs):
		super(BuildingForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'

	class Meta:
		model = Building		

class TenantForm(ModelForm):
	class Meta:
		model = Tenant

BuildingFormSet = modelformset_factory(Building, form=BuildingForm, extra=3)
TenantFormSet = modelformset_factory(Tenant, form=TenantForm)
InlineFormset = inlineformset_factory(Block, Building, extra=1)

class BaseNestedFormset(BaseInlineFormSet):
	
	def add_fields(self, form, index):
		super(BaseNestedFormset, self).add_fields(form, index)

		form.nested = self.nested_formset_class(
			instance=form.instance,
			data=form.data if form.is_bound else None,
			prefix="%s-%s" % (
				form.prefix,
				self.nested_formset_class.get_default_prefix()
				)
			)

	def is_valid(self):
		""" Check if the other nested forms are valid as well
		"""
		result = super(BaseNestedFormset, self).is_valid()
		print("Start result = %s" % result)
		for form in self.forms:
			result = result and form.nested.is_valid()
			print("Is %s valid? %s" % (form.__class__, result))

		return result

	def save(self, commit=True):
		print("Saving main form")
		result = super(BaseNestedFormset, self).save(commit=commit)

		for form in self.forms:
			form.nested.save(commit=commit)
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
		extra=1
		)
	return parent_child
