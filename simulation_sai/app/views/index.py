import json
from django.shortcuts import render
from app.models import comport_settings
import serial.tools.list_ports
from django.views.decorators.csrf import csrf_exempt

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]


def index(request):
    from app.models import UserLogin 
    if request.method == 'GET':
        ports_string = ''

         # Convert QuerySet values to lists
        comport_com_port = list(comport_settings.objects.values_list('com_port', flat=True))
        comport_baud_rate = list(comport_settings.objects.values_list('baud_rate', flat=True))
        comport_parity = list(comport_settings.objects.values_list('parity', flat=True))
        comport_stopbit = list(comport_settings.objects.values_list('stopbits', flat=True))
        comport_databit = list(comport_settings.objects.values_list('bytesize', flat=True))
        comport_card = list(comport_settings.objects.values_list('card', flat=True))

        print(';your card is this:',comport_card)

        print('your baud_rate is this:', comport_baud_rate)
        print('your comport is:', comport_com_port)

        com_ports = get_available_com_ports()
        print('your available COM ports are:', com_ports)

        if com_ports:
            # Get all matching ports
            matching_ports = [port for port in comport_com_port if port in com_ports]
            if matching_ports:
                ports_string = ' '.join(matching_ports)  # Convert list to space-separated string
                print('Matching COM ports found:', ports_string)
            else:
                ports_string = ' '.join(com_ports)  # Convert list to space-separated string
                print('No matching COM port found. Sending all available ports:', ports_string)
        else:
            ports_string = 'No COM ports available'
            print(ports_string)
        # Query all UserLogin entries
        user_logins = UserLogin.objects.all()
        
        # Convert the queryset to a list of dictionaries
        user_logins_list = list(user_logins.values())
        
        # Serialize the list to JSON
        user_logins_json = json.dumps(user_logins_list)
        
        # Pass the serialized JSON data to the template
        context = {
            'user_logins_json': user_logins_json,
            'comport_com_port': ' '.join(comport_com_port),  # Convert list to space-separated string
            'ports_string': ports_string,  
            'comport_baud_rate': ' '.join(map(str, comport_baud_rate)),  # Convert numbers to strings
            'comport_parity': ' '.join(comport_parity),  
            'comport_stopbit': ' '.join(map(str, comport_stopbit)),  
            'comport_databit': ' '.join(map(str, comport_databit)),
            'comport_card': ' '.join(map(str, comport_card)),
        }
        print("context:",context)
        return render(request, 'app/index.html', context)

