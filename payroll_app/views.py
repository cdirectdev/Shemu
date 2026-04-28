from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from calendar import monthrange
from django.contrib.auth.hashers import make_password, check_password 
from .models import Employee, Payslip, Account
account_id = 0

def login_view(request):
    global account_id
    if account_id != 0:
        return redirect('payslips')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = Account.objects.filter(username=username).first()
    
        
        if user and check_password(password, user.password):
            account_id = user.pk
            if user.getIsAdmin():
                messages.success(request, 'Admin login successful!')
                return redirect('employees')  
            else:
                messages.success(request, 'Employee login successful!')
                return redirect('payslips')
        

    
        messages.error(request, "Invalid login")
    return render(request, 'payroll_app/login.html')

MONTHS = [
    "January", "February", "March",
    "April",   "May",      "June",
    "July",    "August",   "September",
    "October", "November", "December"
]

MONTH_MAP = {name: i + 1 for i, name in enumerate(MONTHS)}

def logout_view(request):
    global account_id
    account_id = 0
    messages.success(request, "Logged out successfully.")
    return redirect('login')

def home(request):
    global account_id
    if account_id == 0:
        return redirect('login')
    
    user = get_object_or_404(Account, pk=account_id)
    is_admin = user.getIsAdmin()

    if is_admin:
        all_employees = Employee.objects.all()
        current_employee = None
    else:
        current_employee = user.employee
        all_employees = []
    return render(request, 'payroll_app/home.html', {
        'employees': all_employees,
        'is_admin' : user.getIsAdmin(),
        'is_logged': account_id != 0,
        'current_employee': current_employee,
        'account': user,
    })

def add_overtime(request, pk):
    if request.method == "POST":
        employee=get_object_or_404(Employee, pk=pk)
        overtime_hours = request.POST.get('overtime_hours', 0)
        rate = employee.getRate()
        overtime_pay = (rate/160) * 1.5 * float(overtime_hours)
        employee.overtime_pay += overtime_pay
        employee.save()
        messages.success(request, "Overtime pay added successfully.")
    return redirect('employees')

def create_employee(request):
    global account_id
    if account_id == 0:
        return redirect('login')
    if request.method == "POST":
        name      = request.POST.get('name')
        id_number = request.POST.get('id_number')
        rate      = request.POST.get('rate')
        allowance = request.POST.get('allowance') or None

        if Employee.objects.filter(id_number=id_number).exists():
            messages.error(request, "Employee with this ID number already exists.")
            return redirect('create_employee')

        if Account.objects.filter(username=name).exists():
            messages.error(request, f"Username '{name}' already taken.")
            return redirect('create_employee')
    
        try:
            # Create Account (username = name, password = "123")
            account = Account(
                username=name,  # e.g., "John Doe"
                is_admin=False
            )
            account.set_password("123")  # Hashed password
            account.save()

            # Create Employee and linked to account
            Employee.objects.create(
                account=account,
                id_number=id_number,
                name=name,
                rate=rate,
                allowance=allowance,
                overtime_pay=0.0
            )
            
            messages.success(request, 
                f"Employee '{name}' created successfully!<br>")
            return redirect('employees')

        except Exception as e:
            messages.error(request, f"Error creating employee: {str(e)}")
            return redirect('create_employee')

    user = get_object_or_404(Account, pk=account_id)
    return render(request, 'payroll_app/create_employee.html', {
        'is_admin' : user.getIsAdmin(),
        'is_logged': account_id != 0,
    })

def update_employee(request, pk):
    global account_id
    if account_id == 0:
        return redirect('login')
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
    user = get_object_or_404(Account, pk=account_id)
    return render(request, 'payroll_app/update_employee.html', {
        'employee': employee,
        'is_admin' : user.getIsAdmin(),
        'is_logged': account_id != 0,
    })


def delete_employee(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.delete()
    return redirect('employees')


def payslips(request):
    global account_id
    if account_id == 0:
        return redirect('login')

    user = get_object_or_404(Account, pk=account_id)
    is_admin = user.getIsAdmin()

    if is_admin: # For the admin
        employees = Employee.objects.all()
        slips = Payslip.objects.all().order_by('-pk')
        can_generate = True
        current_employee = None
    else: # For the employees
        employee = user.employee
        employees = [employee]
        slips = Payslip.objects.filter(id_number=employee).order_by('-pk')
        can_generate = False
        current_employee = employee

    if request.method == "POST" and is_admin:
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
        'is_admin' : user.getIsAdmin(),
        'is_logged': account_id != 0,
        'current_employee': current_employee,
        'can_generate': can_generate,  # Controls form visibility
        'account': user,
    })


def view_payslip(request, pk):
    global account_id
    if account_id == 0:
        return redirect('login')

    user = get_object_or_404(Account, pk=account_id)
    slip = get_object_or_404(Payslip, pk=pk)

    # safely get the linked employee — returns None if admin (no employee linked)
    try:
        current_employee = user.employee
    except Exception:
        current_employee = None

    # if not admin, check that this payslip belongs to them
    if not user.getIsAdmin():
        if current_employee is None or slip.id_number != current_employee:
            messages.error(request, "You can only view your own payslips.")
            return redirect('payslips')

    gross_pay = slip.getCycleRate() + slip.getEarnings_allowance() + slip.getOvertime()

    if slip.getPay_cycle() == 1:
        total_deductions = slip.getDeductions_tax() + slip.getPag_ibig()
    else:
        total_deductions = slip.getDeductions_tax() + slip.getDeductions_health() + slip.getSSS()

    return render(request, 'payroll_app/view_payslip.html', {
        'slip'            : slip,
        'gross_pay'       : gross_pay,
        'total_deductions': total_deductions,
        'is_admin'        : user.getIsAdmin(),
        'is_logged'       : account_id != 0,
        'account'         : user,
        'current_employee': current_employee,   # ← None for admin, Employee obj for employee
    })