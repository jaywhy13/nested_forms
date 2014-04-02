from django.db import models

# Create your models here.
class Block(models.Model):
	name = models.CharField("Block Name", max_length=255)

	def __unicode__(self):
		return "Block: %s" % self.name


class Building(models.Model):
	name = models.CharField("Bldg Name", max_length=255)
	street_name = models.CharField("Bldg Street", max_length=255)
	block = models.ForeignKey("Block", blank=True, null=True, 
		related_name="buildings")

	def __unicode__(self):
		return "Building: %s" % self.name

class Tenant(models.Model):
	first_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	building = models.ForeignKey("Building", blank=True, null=True, 
		related_name="tenants")

	@property
	def name(self):
		return "%s, %s" % (self.last_name, self.first_name)

	def __unicode__(self):
		return "Tenant: %s" % self.name

class Furniture(models.Model):

	name = models.CharField(max_length=255)
	tenant = models.ForeignKey("Tenant", blank=True, null=True, 
		related_name="furniture")

	def __unicode__(self):
		return "Furniture: %s" % self.name
