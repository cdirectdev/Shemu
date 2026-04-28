from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from calendar import monthrange

from .models import Employee, Payslip

MONTHS = [
    "January", "February", "March",
    "April",   "May",      "June",
    "July",    "August",   "September",
    "October", "November", "December"
]

MONTH_MAP = {name: i + 1 for i, name in enumerate(MONTHS)}


def home(request):
    all_employees = Employee.objects.all()
    return render(request, 'payroll_app/home.html', {
        'employees': all_employees
    })

def add_overtime(request, pk):
    pass

def create_employee(request):
    if request.method == "POST":
        name      = request.POST.get('name')
        id_number = request.POST.get('id_number')
        rate      = request.POST.get('rate')
        allowance = request.POST.get('allowance')

        if Employee.objects.filter(id_number=id_number).exists():
            messages.error(request, "Employee with this ID number already exists.")
            return redirect('create_employee')

        Employee.objects.create(
            id_number=id_number,
            name=name,
            rate=rate,
            allowance=allowance
        )
        messages.success(request, "Employee created successfully.")
        return redirect('employees')

    return render(request, 'payroll_app/create_employee.html')
def update_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.name      = request.POST.get('name')
        employee.id_number = request.POST.get('id_number')
        employee.rate      = request.POST.get('rate')
        employee.allowance = request.POST.get('allowance')

        if Employee.objects.filter(id_number=employee.id_number).exclude(pk=employee.pk).exists():
            messages.error(request, "Another employee with this ID number already exists.")
            return redirect('update_employee', pk=employee.pk)

        employee.save()
        messages.success(request, "Employee updated successfully.")
        return redirect('employees')
    return render(request, 'payroll_app/update_employee.html', {'employee': employee})


def delete_employee(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.delete()
    return redirect('employees')


def payslips(request):
    employees = Employee.objects.all()
    slips     = Payslip.objects.all().order_by('-pk')

    if request.method == "POST":
        payroll_for = request.POST.get('payroll_for')
        month       = request.POST.get('month')
        year        = request.POST.get('year')
        cycle       = int(request.POST.get('cycle'))

        # validate month
        if month not in MONTH_MAP:
            messages.error(request, "Invalid month selected.")
            return redirect('payslips')

        # build date range
        last_day   = monthrange(int(year), MONTH_MAP[month])[1]
        date_range = "1-15" if cycle == 1 else f"16-{last_day}"

        # pick employees
        if payroll_for == "all":
            selected = employees
        else:
            selected = Employee.objects.filter(id_number=payroll_for)

        created         = 0
        duplicate_found = False

        for emp in selected:

            # skip if payslip already exists for this period
            if Payslip.objects.filter(
                id_number=emp,
                month=month,
                year=year,
                pay_cycle=cycle
            ).exists():
                duplicate_found = True
                continue

            # base values
            half_rate = emp.rate / 2
            allowance = emp.getAllowance()
            overtime  = emp.getOvertime()

            # deductions per cycle
            pagibig    = 0.0
            philhealth = 0.0
            sss        = 0.0

            if cycle == 1:
                # Cycle 1 — pag-ibig flat fee
                pagibig = 100.0
                taxable = half_rate + allowance + overtime - pagibig
            else:
                # Cycle 2 — philhealth + sss based on full rate
                philhealth = emp.rate * 0.04
                sss        = emp.rate * 0.045
                taxable    = half_rate + allowance + overtime - philhealth - sss

            # tax and final pay
            tax   = taxable * 0.2
            total = taxable - tax

            Payslip.objects.create(
                id_number         = emp,
                month             = month,
                date_range        = date_range,
                year              = year,
                pay_cycle         = cycle,
                rate              = emp.rate,
                earnings_allowance= allowance,
                deductions_tax    = tax,
                deductions_health = philhealth,
                pag_ibig          = pagibig,
                sss               = sss,
                overtime          = overtime,
                total_pay         = total,
            )

            emp.resetOvertime()
            created += 1

        if created:
            messages.success(request, f"{created} payslip(s) generated successfully.")
        if duplicate_found:
            messages.warning(request, "Some payslips already existed and were skipped.")

        return redirect('payslips')

    return render(request, 'payroll_app/payslips.html', {
        'employees': employees,
        'slips'    : slips,
        'months'   : MONTHS,      # ← used by the month <select> in the template
    })


def view_payslip(request, pk):
    slip = get_object_or_404(Payslip, pk=pk)
    gross_pay = slip.getCycleRate() + slip.getEarnings_allowance() + slip.getOvertime()

    if slip.getPay_cycle() == 1:
        total_deductions = slip.getDeductions_tax() + slip.getPag_ibig()
    else:
        total_deductions = slip.getDeductions_tax() + slip.getDeductions_health() + slip.getSSS()

    return render(request, 'payroll_app/view_payslip.html', {
        'slip'            : slip,
        'gross_pay'       : gross_pay,
        'total_deductions': total_deductions,
    })