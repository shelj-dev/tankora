import json
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings

from django.contrib.auth import login, authenticate
from django.utils import timezone
from .models import GasDevice, LeakageAlert, TelemetryLog
from .services import predict_gas_last_days, send_email, send_rebook_email
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from .mqtt_client import mqtt_send_value


def dashboard(request):
    devices = GasDevice.objects.all()
    device_data = []
    
    active_alerts = LeakageAlert.objects.filter(resolved=False).order_by('-timestamp')

    for device in devices:
        prediction = predict_gas_last_days(device)

        try:
            total_capacity = device.full_weight - device.gross_weight
            if device.gross_weight > device.current_weight:
                gas_balance_percent = 0
            else:
                remaining_gas = device.current_weight - device.gross_weight
                gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
                gas_balance_percent = round(gas_balance_percent)
        except:
            gas_balance_percent = 0

        device_data.append({
            'device': device,
            'prediction': prediction,
            'gas_balance': gas_balance_percent,
        })
        
    context = {
        'device_data': device_data,
        'active_alerts': active_alerts,
    }
    # return render(request, 'app/dashboard.html', context)
    return render(request, 'app/newest_dashboard.html', context)


# def new_dashboard(request):
#     devices = GasDevice.objects.all()
#     device_data = []
    
#     active_alerts = LeakageAlert.objects.filter(resolved=False).order_by('-timestamp')

#     for device in devices:
#         prediction = predict_gas_last_days(device)

#         device_data.append({
#             'device': device,
#             'prediction': prediction,
#             'gas_balance': (100),
#         })
        
#     context = {
#         'device_data': device_data,
#         'active_alerts': active_alerts,
#     }
#     return render(request, 'app/new_dashboard.html', context)


def toggle_valve(request, device_id):
    if request.method == 'POST':
        device = get_object_or_404(GasDevice, device_id=device_id)
        action = request.POST.get('action')
        
        if action == 'OPEN':
            new_status = 'OPEN'
        elif action == 'CLOSED':
            new_status = 'CLOSED'
        else:
            # Fallback to flip if no action specified
            new_status = 'OPEN' if device.valve_status == 'CLOSED' else 'CLOSED'
        
        try:
            # Pass the desired status to MQTT
            mqtt_send_value(new_status)
            
            device.valve_status = new_status
            device.save()
            
        except Exception as e:
            print(f"Failed to publish MQTT message: {e}")
            
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# def update_sensor_data(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         device_id = data.get('device_id')
#         gas_level = data.get('gas_level')
#         leak_detected = data.get('leak_detected')
        
#         device = GasDevice.objects.get(device_id=device_id)
#         device.gas_level = gas_level
#         device.leak_detected = leak_detected
#         device.save()
        
#         return JsonResponse({'status': 'success'})
#     return JsonResponse({'status': 'error'})


def dashboard_data(request):
    devices = GasDevice.objects.all()
    device_data = []
    
    active_alerts = LeakageAlert.objects.filter(resolved=False).order_by('-timestamp')
    alert_msgs = []
    for alert in active_alerts:
        alert_msgs.append({
            'device_id': alert.device.device_id,
            'timestamp': alert.timestamp.strftime("%b %d, %H:%M")
        })

    for device in devices:
        from .services import predict_gas_last_days
        prediction = predict_gas_last_days(device)

        try:
            total_capacity = device.full_weight - device.gross_weight # 50 - 20
            
            if device.gross_weight > device.current_weight:
                remaining_gas = "None"
                gas_balance_percent = "None"
            else:
                remaining_gas = device.current_weight - device.gross_weight # 0 - 20
                gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
                gas_balance_percent = round(gas_balance_percent)
                # (-20 / 30) * 100
        except:
            gas_balance_percent = 0
            
        # print("Q", gas_balance_percent)
        # print("gross_weight", device.gross_weight)
        # print("current_weight", device.current_weight)

        leak_detected = any(alert.device.device_id == device.device_id for alert in active_alerts)

        device_data.append({
            'device_id': device.device_id,
            'current_level': round(device.current_level, 1),
            'valve_status': device.valve_status,
            'prediction': prediction,
            'booking_threshold': device.booking_threshold,
            'gas_balance': gas_balance_percent,
            'current_weight': device.current_weight,
            'leak_detected': leak_detected,
        })
        
    return JsonResponse({
        'devices': device_data,
        'alerts': alert_msgs
    })





def testing_email(request):
    res = send_email()
    return JsonResponse({"Message": res})


def rebook(request):
    send_rebook_email()
    return redirect("dashboard")



def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, "app/login.html", {
                "error": "INVALID CREDENTIALS"
            })

    return render(request, "app/login.html")



from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    devices = GasDevice.objects.all()
    active_alerts = LeakageAlert.objects.filter(resolved=False).order_by('-timestamp')
    
    device_data = []
    for device in devices:
        from .services import predict_gas_last_days
        prediction = predict_gas_last_days(device)
        
        try:
            total_capacity = device.full_weight - device.gross_weight
            if device.gross_weight > device.current_weight:
                gas_balance_percent = 0
            else:
                remaining_gas = device.current_weight - device.gross_weight
                gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
                gas_balance_percent = round(gas_balance_percent)
        except:
            gas_balance_percent = 0
            
        device_data.append({
            'device': device,
            'prediction': prediction,
            'gas_balance': gas_balance_percent,
        })

    context = {
        'device_data': device_data,
        'active_alerts': active_alerts,
    }
    return render(request, "app/admin_dashboard.html", context)


from .forms import GasDeviceForm

@login_required
def gas_devices_list(request):
    devices = GasDevice.objects.all()
    return render(request, "app/gas_devices_list.html", {'devices': devices})

@login_required
def gas_device_edit(request, device_id):
    device = get_object_or_404(GasDevice, pk=device_id)
    if request.method == "POST":
        form = GasDeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            return redirect('gas_devices_list')
    else:
        form = GasDeviceForm(instance=device)
    
    return render(request, "app/gas_device_edit.html", {
        'form': form,
        'device': device
    })

@login_required
def leakage_alerts(request):
    alerts = LeakageAlert.objects.all().order_by('-timestamp')
    return render(request, "app/leakage_alerts.html", {'alerts': alerts})

@login_required
def resolve_alert(request, alert_id):
    if request.method == "POST":
        alert = get_object_or_404(LeakageAlert, id=alert_id)
        alert.resolved = True
        alert.save()
    return redirect('leakage_alerts')

@login_required
def telemetry_logs(request):
    logs = TelemetryLog.objects.all().order_by('-timestamp')[:100]  # Limit to 100
    return render(request, "app/telemetry_logs.html", {'logs': logs})

@login_required
def rebook(request):
    devices = GasDevice.objects.filter(user=request.user)
    if request.method == "POST":
        device_id = request.POST.get('device_id')
        device = get_object_or_404(GasDevice, id=device_id)
        from .services import send_rebook_email
        if send_rebook_email():
            device.last_rebook_sent = timezone.now()
            device.save()
            # In a real app, you'd add a success message here
            return redirect('admin_dashboard')
            
    return render(request, "app/rebook.html", {'devices': devices})