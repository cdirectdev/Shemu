from django.shortcuts import render, redirect
from .models import Employee

# Create your views here.

def home(request):
    all_employees = Employee.objects.all()
    return render(request, 'payroll_app/home.html', {'employees': all_employees})