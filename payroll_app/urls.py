"""
URL configuration for Shemu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home, name='employees'),
    path('payslips/', views.payslips, name='payslips'),
    path('view-payslip/<int:pk>/', views.view_payslip, name='view_payslip'),
    path('create-employee/', views.create_employee, name='create_employee'),
    path('update-employee/<int:pk>/', views.update_employee, name='update_employee'),
    path('delete-employee/<int:pk>/', views.delete_employee, name='delete_employee'),
    path('add-overtime/<int:pk>/', views.add_overtime, name='add_overtime'),
    path('login/', views.loginpage, name='login'),
]
