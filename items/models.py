from django.db import models

# Create your models here.
from django.db import models

class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, default='New')
    
    # This is our bridge to SharePoint
    sharepoint_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.title