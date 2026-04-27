from django.shortcuts import render, redirect, get_object_or_404   
from .models import Employee, Payslip

# Create your views here.

def home(request):
    all_employees = Employee.objects.all()
    return render(request, 'payroll_app/home.html', {'employees': all_employees})

def payslips(request):
    employees = Employee.objects.all()
    slips = Payslip.objects.all().order_by('-pk')

    if request.method == "POST":
        payroll_for = request.POST['payroll_for']
        month = request.POST['month']
        year = request.POST['year']
        cycle = int(request.POST['cycle'])

        if cycle == 1:
            date_range = "1-15"
        else:
            date_range = "16-30"

        if payroll_for == "all":
            selected = employees
        else:
            selected = Employee.objects.filter(id_number=payroll_for)

        for emp in selected:

            if Payslip.objects.filter(
                id_number=emp,
                month=month,
                year=year,
                pay_cycle=cycle
            ).exists():
                continue

            half_rate = emp.rate / 2
            allowance = emp.getAllowance()
            overtime = emp.getOvertime()
            tax = emp.rate * 0.20

            health = 0
            pagibig = 0
            sss = 0

            if cycle == 1:
                pagibig = 100
            else:
                health = emp.rate * 0.04
                sss = emp.rate * 0.045

            total = half_rate + allowance + overtime - tax - health - pagibig - sss

            Payslip.objects.create(
                id_number=emp,
                month=month,
                date_range=date_range,
                year=year,
                pay_cycle=cycle,
                rate=emp.rate,
                earnings_allowance=allowance,
                deductions_tax=tax,
                deductions_health=health,
                pag_ibig=pagibig,
                sss=sss,
                overtime=overtime,
                total_pay=total
            )

            emp.resetOvertime()
            emp.save()

        return redirect('payslips')

    return render(request, 'payroll_app/payslips.html', {
        'employees': employees,
        'slips': slips
    })


def view_payslip(request, pk):
    slip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll_app/view_payslip.html', {'slip': slip})
