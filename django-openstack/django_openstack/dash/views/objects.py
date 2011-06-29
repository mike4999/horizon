# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Views for managing Swift containers.
"""
import logging

from django import http
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.shortcuts import render_to_response

from django_openstack import api
from django_openstack import forms


LOG = logging.getLogger('django_openstack.dash')


class DeleteObject(forms.SelfHandlingForm):
    object_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        api.swift_delete_object(
                request.POST['container_name'],
                data['object_name'])
        messages.info(request,
                      'Successfully deleted object: %s' % \
                      data['object_name'])
        return shortcuts.redirect(request.build_absolute_uri())


class UploadObject(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label="Object Name")
    object_file = forms.FileField(label="File")

    def handle(self, request, data):
        api.swift_upload_object(
                request.POST['container_name'],
                data['name'],
                request.FILES['object_file'].read())
        messages.success(request, "Object was successfully uploaded.")
        return shortcuts.redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id, container_name):
    delete_form, handled = DeleteObject.maybe_handle(request)
    if handled:
        return handled

    objects = api.swift_get_objects(container_name)

    return render_to_response('dash_objects.html', {
        'container_name': container_name,
        'objects': objects,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
def upload(request, tenant_id, container_name):
    form, handled = UploadObject.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('dash_objects_upload.html', {
        'container_name': container_name,
        'upload_form': form,
    }, context_instance=template.RequestContext(request))


@login_required
def download(request, tenant_id, container_name, object_name):
    object_data = api.swift_get_object_data(
            container_name, object_name)

    response = http.HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            object_name
    for data in object_data:
        response.write(data)
    return response
