"""
Personnel Views
"""
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Personnel


class PersonnelListView(LoginRequiredMixin, ListView):
    """List all personnel"""
    model = Personnel
    template_name = 'personnel/personnel_profile_list.html'
    context_object_name = 'personnel_list'
    paginate_by = 100
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-created_at')


class PersonnelDetailView(LoginRequiredMixin, DetailView):
    """View personnel details"""
    model = Personnel
    template_name = 'personnel/personnel_profile_detail.html'
    context_object_name = 'personnel'
    
    def get_context_data(self, **kwargs):
        """Add QR code object to context"""
        context = super().get_context_data(**kwargs)
        # Import here to avoid circular imports
        from qr_manager.models import QRCodeImage
        try:
            context['qr_code_obj'] = QRCodeImage.objects.get(
                qr_type=QRCodeImage.TYPE_PERSONNEL,
                reference_id=self.object.id
            )
        except QRCodeImage.DoesNotExist:
            context['qr_code_obj'] = None
        return context

