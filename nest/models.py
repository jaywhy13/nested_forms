from django.db import models

# Create your models here.
class Block(models.Model):
	name = models.CharField("Block Name", max_length=255)


class Building(models.Model):
	name = models.CharField("Bldg Name", max_length=255)
	block = models.ForeignKey("Block", blank=True, null=True, 
		related_name="buildings")

class Tenant(models.Model):
	first_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	building = models.ForeignKey("Building", blank=True, null=True, 
		related_name="tenants")

