from django.urls import path

from apps.invoices import views
# TEMP: preview routes disabled — using views.py USE_MOCK_DATA toggle instead now.
# Uncomment the import below + the two preview/ paths if you want the old
# separate /invoices/preview/ routes back instead.
# from apps.invoices import preview

app_name = "invoices"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("new/", views.invoice_create, name="create"),
    path("<str:id>/", views.invoice_detail, name="detail"),
    path("<str:id>/reissue/", views.invoice_reissue, name="reissue"),
    path("<str:id>/print/", views.invoice_print, name="print"),
    # --- PREVIEW ONLY, no database calls — remove these two lines + preview.py when done ---
    # path("preview/", preview.preview_invoice_list, name="preview_list"),
    # path("preview/<str:id>/", preview.preview_invoice_detail, name="preview_detail"),
]