from django.shortcuts import render, redirect, get_object_or_404   
from .models import Employee, Payslip

# Create your views here.

def home(request):
    all_employees = Employee.objects.all()
    return render(request, 'payroll_app/home.html', {'employees': all_employees})