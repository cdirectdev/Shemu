from django.db import models

# Create your models here.
class Employee(models.Model):
    name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=12)
    rate = models.FloatField()
    overtime_pay = models.FloatField(null=True, blank=True)
    allowance = models.FloatField(null=True, blank=True)\

    def getName(self):
        return self.name
    def getID(self):
        return self.id_number
    def getRate(self):
        return self.rate
    def getOvertime(self):
        return self.overtime_pay
    def resetOvertime(self):
        self.overtime_pay = 0
    def getAllowance(self):
        return self.allowance
    def __str__(self):
        return f"pk: {self.getID()}, rate: {self.getRate()}"