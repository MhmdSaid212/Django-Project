from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.attachments.constants import CATEGORY_CHOICES, ENTITY_CHOICES
from apps.attachments.forms import AttachmentUploadForm
from apps.attachments.services import AttachmentService
from core.access import ALL_ROLES
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import get_session_user, login_required, role_required
from core.utils import parse_object_id


def _unavailable(request, next_name="attachments:list"):
    messages.error(request, "Cannot reach MongoDB. Attachments are unavailable.")
    return redirect(next_name)


def _safe_next(request, fallback="attachments:list"):
    candidate = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return reverse(fallback)


@login_required
@role_required(*ALL_ROLES)
def attachment_list(request):
    entity_type = (request.GET.get("entity_type") or "").strip()
    entity_id = (request.GET.get("entity_id") or "").strip()
    category = (request.GET.get("category") or "").strip().upper()
    form = AttachmentUploadForm(
        initial={
            "entity_type": entity_type or None,
            "entity_id": entity_id,
            "category": category or None,
        }
    )
    try:
        if entity_id:
            parse_object_id(entity_id, field="entity_id")
        items = AttachmentService().list_presented(
            entity_type=entity_type or None,
            entity_id=entity_id or None,
            category=category or None,
        )
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Attachments are unavailable.")
        items = []
    except TourOpsError as extra:
        messages.error(request, extra.message)
        items = []
        entity_id = ""
    return render(
        request,
        "attachments/list.html",
        {
            "page_title": "Attachments",
            "page_heading": "Documents",
            "attachments": items,
            "form": form,
            "entity_choices": ENTITY_CHOICES,
            "category_choices": CATEGORY_CHOICES,
            "filters": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "category": category,
            },
        },
    )


@login_required
@role_required(*ALL_ROLES)
@require_http_methods(["POST"])
def attachment_upload(request):
    hide_entity = bool(request.POST.get("entity_type") and request.POST.get("entity_id") and request.POST.get("next"))
    form = AttachmentUploadForm(request.POST, request.FILES, hide_entity=hide_entity)
    next_url = _safe_next(request)
    if not form.is_valid():
        messages.error(request, "Could not upload the file. Check the type, size, and linked record.")
        return redirect(next_url)
    try:
        AttachmentService().create(
            actor_id=get_session_user(request)["id"],
            entity_type=form.cleaned_data["entity_type"],
            entity_id=form.cleaned_data["entity_id"],
            category=form.cleaned_data["category"],
            upload=form.cleaned_data["upload"],
            notes=form.cleaned_data.get("notes"),
        )
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect(next_url)
    messages.success(request, "File uploaded.")
    return redirect(next_url)


@login_required
@role_required(*ALL_ROLES)
def attachment_download(request, id):
    try:
        return AttachmentService().file_response(id)
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect(_safe_next(request))


@login_required
@role_required(*ALL_ROLES)
@require_POST
def attachment_delete(request, id):
    next_url = _safe_next(request)
    try:
        AttachmentService().soft_delete(id, actor_id=get_session_user(request)["id"])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect(next_url)
    messages.success(request, "Attachment removed.")
    return redirect(next_url)
