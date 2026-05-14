from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Inspection
from .forms import InspectionForm
from .ai_module import analyze_image


@login_required
def index(request):
    if request.user.role == 'admin':
        inspections = Inspection.objects.select_related('vehicle', 'user').all()
    else:
        inspections = Inspection.objects.select_related('vehicle', 'user').filter(user=request.user)

    return render(request, 'vehicles/index.html', {'inspections': inspections})


@login_required
def upload(request):
    form = InspectionForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        inspection = form.save(commit=False)
        inspection.user = request.user
        inspection.save()

        # Read language from POST or cookie
        language = request.POST.get('language') or request.COOKIES.get('lang', 'ru')

        result = analyze_image(inspection.image.path, language=language)
        inspection.result = result["text"]
        inspection.confidence = result["confidence"]
        inspection.save()

        response = redirect('result', inspection.id)
        response.set_cookie('lang', language, max_age=60*60*24*365)
        return response

    return render(request, 'vehicles/upload.html', {'form': form})


@login_required
def result(request, pk):
    inspection = get_object_or_404(Inspection, id=pk)
    return render(request, 'vehicles/result.html', {'inspection': inspection})