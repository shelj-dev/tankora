import json
import paho.mqtt.client as mqtt
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from .models import GasDevice, LeakageAlert
from .services import predict_gas_last_days
from django.http import JsonResponse


def dashboard(request):
    devices = GasDevice.objects.all()
    device_data = []
    
    active_alerts = LeakageAlert.objects.filter(resolved=False).order_by('-timestamp')

    for device in devices:
        prediction = predict_gas_last_days(device)

        try:
            total_capacity = device.full_weight - device.gross_weight # 50 -15
            remaining_gas = device.current_weight - device.gross_weight # 15 - 15

            gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
        except:
            gas_balance_percent = 0
            
        print(device.gross_weight)
                    
        device_data.append({
            'device': device,
            'prediction': prediction,
            'gas_balance': round(gas_balance_percent, 2),
        })
        
    context = {
        'device_data': device_data,
        'active_alerts': active_alerts,
    }
    return render(request, 'app/dashboard.html', context)


def toggle_valve(request, device_id):
    if request.method == 'POST':
        device = get_object_or_404(GasDevice, device_id=device_id)
        
        # Determine new status
        new_status = 'OPEN' if device.valve_status == 'CLOSED' else 'CLOSED'
        
        # Publish MQTT command to Pico 2W
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            MQTT_BROKER = getattr(settings, 'MQTT_BROKER', 'test.mosquitto.org')
            MQTT_PORT = getattr(settings, 'MQTT_PORT', 1883)
            MQTT_COMMAND_TOPIC = getattr(settings, 'MQTT_COMMAND_TOPIC', 'tankora/{}/command')
            
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            command_payload = json.dumps({
                "command": f"{new_status}_VALVE", 
                "buzzer": "OFF"
            })
            client.publish(MQTT_COMMAND_TOPIC.format(device.device_id), command_payload)
            client.disconnect()
            
            # Update DB Optimistically (or wait for telemetry to update it)
            device.valve_status = new_status
            device.save()
            
        except Exception as e:
            print(f"Failed to publish MQTT message: {e}")
            
    return redirect('dashboard')


def update_sensor_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        device_id = data.get('device_id')
        gas_level = data.get('gas_level')
        leak_detected = data.get('leak_detected')
        
        device = GasDevice.objects.get(device_id=device_id)
        device.gas_level = gas_level
        device.leak_detected = leak_detected
        device.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


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
            total_capacity = device.full_weight - device.gross_weight
            remaining_gas = device.current_weight - device.gross_weight

            gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
        except:
            gas_balance_percent = 0

        device_data.append({
            'device_id': device.device_id,
            'current_level': round(device.current_level, 1),
            'valve_status': device.valve_status,
            'prediction': prediction,
            'booking_threshold': device.booking_threshold,
            'gas_balance': round(gas_balance_percent, 2), 
        })
        
    return JsonResponse({
        'devices': device_data,
        'alerts': alert_msgs
    })
