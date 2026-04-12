from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Inspection
from .forms import InspectionForm
from .ai_module import analyze_image

@login_required
def index(request):
    if request.user.role == 'admin':
        inspections = Inspection.objects.all()
    else:
        inspections = Inspection.objects.filter(vehicle__owner=request.user)

    return render(request, 'vehicles/index.html', {'inspections': inspections})
@login_required
def upload(request):
    form = InspectionForm(request.POST or None, request.FILES or None, user=request.user)

    if form.is_valid():
        inspection = form.save()

        result = analyze_image(inspection.image.path)

        inspection.result = result["text"]
        inspection.confidence = result["confidence"]  # добавь поле!
        inspection.save()
        return redirect('result', inspection.id)

    return render(request, 'vehicles/upload.html', {'form': form})
@login_required
def result(request, pk):
    inspection = Inspection.objects.get(id=pk)
    return render(request, 'vehicles/result.html', {'inspection': inspection})
