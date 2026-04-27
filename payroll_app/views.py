from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from calendar import monthrange

from .models import Employee, Payslip

def home(request):
    all_employees = Employee.objects.all()
    return render(request, 'payroll_app/home.html', {
        'employees': all_employees
    })



def payslips(request):
    employees = Employee.objects.all()
    slips = Payslip.objects.all().order_by('-pk')

    if request.method == "POST":

        payroll_for = request.POST.get('payroll_for')
        month = request.POST.get('month')
        year = request.POST.get('year')
        cycle = int(request.POST.get('cycle'))

        month_map = {
            "January": 1, "February": 2, "March": 3,
            "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9,
            "October": 10, "November": 11, "December": 12
        }


        if month not in month_map:
            messages.error(request, "Invalid month selected.")
            return redirect('payslips')

    
        last_day = monthrange(int(year), month_map[month])[1]

        if cycle == 1:
            date_range = "1-15"
        else:
            date_range = f"16-{last_day}"

        if payroll_for == "all":
            selected = employees
        else:
            selected = Employee.objects.filter(id_number=payroll_for)

        created = 0
        duplicate_found = False

        for emp in selected:

            if Payslip.objects.filter(
                id_number=emp,
                month=month,
                year=year,
                pay_cycle=cycle
            ).exists():
                duplicate_found = True
                continue

            half_rate = emp.rate / 2
            allowance = emp.getAllowance()
            overtime = emp.getOvertime()

            tax = emp.rate * 0.20
            pagibig = 0
            philhealth = 0
            sss = 0

            if cycle == 1:
                pagibig = 100
            else:
                philhealth = emp.rate * 0.04
                sss = emp.rate * 0.045

    
            total = (
                half_rate
                + allowance
                + overtime
                - tax
                - pagibig
                - philhealth
                - sss
            )

            Payslip.objects.create(
                id_number=emp,
                month=month,
                date_range=date_range,
                year=year,
                pay_cycle=cycle,
                rate=emp.rate,
                earnings_allowance=allowance,
                deductions_tax=tax,
                deductions_health=philhealth,
                pag_ibig=pagibig,
                sss=sss,
                overtime=overtime,
                total_pay=total
            )

            emp.overtime_pay = 0
            emp.save()

            created += 1

        if created:
            messages.success(
                request,
                f"{created} payslip(s) generated successfully."
            )

        if duplicate_found:
            messages.warning(
                request,
                "Some payslips already existed and were skipped."
            )

        return redirect('payslips')

    return render(request, 'payroll_app/payslips.html', {
        'employees': employees,
        'slips': slips
    })


def view_payslip(request, pk):
    slip = get_object_or_404(Payslip, pk=pk)

    return render(request, 'payroll_app/view_payslip.html', {
        'slip': slip
    })