import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .ai_module import analyze_image
from .forms import InspectionForm
from .models import Inspection, Vehicle

VALID_LANGUAGES = {'ru', 'uz', 'en'}
VALID_MODES = {'simple', 'detailed'}


def home(request):
    """Public landing page with simulations / hero / schemas.
    
    If the user is logged in we still show the landing page but it nudges them
    toward the inspection list & upload pages.
    """
    return render(request, 'vehicles/home.html', {
        'is_authenticated': request.user.is_authenticated,
    })


@login_required
def index(request):
    """List of past inspections — admins see all, users see their own."""
    if request.user.role == 'admin':
        inspections = Inspection.objects.select_related('vehicle', 'user').all()
    else:
        inspections = Inspection.objects.select_related('vehicle', 'user').filter(
            user=request.user
        )
    return render(request, 'vehicles/index.html', {'inspections': inspections})


def _resolve_language(request):
    lang = request.POST.get('language', '').strip()
    if lang not in VALID_LANGUAGES:
        lang = request.COOKIES.get('lang', 'ru').strip()
    if lang not in VALID_LANGUAGES:
        lang = 'ru'
    return lang


def _resolve_mode(request, default='simple'):
    mode = (request.POST.get('mode') or request.GET.get('mode') or default).strip()
    if mode not in VALID_MODES:
        mode = default
    return mode


@login_required
def upload(request):
    """Upload endpoint. The same view handles both simple and detailed modes;
    the template renders the right UI based on `mode`."""
    initial_mode = _resolve_mode(request, default='simple')
    form = InspectionForm(
        request.POST or None,
        request.FILES or None,
        initial={'mode': initial_mode},
    )

    if request.method == 'POST' and form.is_valid():
        inspection = form.save(commit=False)
        inspection.user = request.user
        # Ensure mode is set from the POST
        inspection.mode = _resolve_mode(request, default='simple')
        inspection.save()

        language = _resolve_language(request)

        # Build details dict for the prompt
        vehicle_label = (inspection.custom_vehicle or '').strip()
        if not vehicle_label and inspection.vehicle:
            vehicle_label = inspection.vehicle.name
        details = {
            'vehicle': vehicle_label,
            'brand': inspection.brand,
            'model': inspection.model_name,
            'year': inspection.year,
            'color': inspection.color,
            'mileage': inspection.mileage,
            'fuel': inspection.fuel_type,
            'transmission': inspection.transmission,
            'extra': inspection.additional_info,
        }

        result = analyze_image(
            inspection.image.path,
            language=language,
            mode=inspection.mode,
            details=details,
        )
        inspection.result = result['text']
        inspection.confidence = result['confidence']
        inspection.metrics_json = json.dumps(result.get('metrics') or {})
        inspection.save()

        response = redirect('result', inspection.id)
        response.set_cookie('lang', language, max_age=60 * 60 * 24 * 365)
        return response

    vehicles = Vehicle.objects.all().order_by('name')
    return render(request, 'vehicles/upload.html', {
        'form': form,
        'vehicles': vehicles,
        'mode': initial_mode,
    })


@login_required
def result(request, pk):
    inspection = get_object_or_404(Inspection, id=pk)
    # Permission: users see only their own, admin sees all
    if inspection.user_id != request.user.id and request.user.role != 'admin':
        return redirect('index')

    try:
        metrics = json.loads(inspection.metrics_json) if inspection.metrics_json else {}
    except Exception:
        metrics = {}
    return render(request, 'vehicles/result.html', {
        'inspection': inspection,
        'metrics_json': json.dumps(metrics),
        'metrics': metrics,
    })
