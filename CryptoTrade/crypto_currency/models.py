from django.db import models

# Create your models here.
class Network(models.Model):
    name=models.CharField(max_length=200, null = True, blank = True)
    website=models.URLField(blank=True)
    api_key=models.CharField(max_length=200, null = True, blank = True)
    network_description=models.CharField(max_length=200, null = True, blank = True)
    acronym=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.name
    


class Cryptocurrency(models.Model):
    symbol=models.CharField(max_length=20, null = True, blank = True)
    id_pk=models.CharField(max_length=50, unique=True) #For API identifiers
    is_tradable=models.BooleanField(default=True)
    crypto_description=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.symbol
    
