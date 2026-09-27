from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.constants import ALL_STAFF
from core.viewsets import StaffModelViewSet
from documents.models import Document
from documents.serializers import DocumentSerializer


class DocumentViewSet(StaffModelViewSet):
    """Upload and download files. Policy, claim, and underwriting documents must name the record they belong to."""

    queryset = Document.objects.select_related("policy", "claim", "underwriting_request")
    serializer_class = DocumentSerializer
    write_roles = ALL_STAFF
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["type", "policy", "claim", "underwriting_request"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name", "size"]

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        document = self.get_object()
        if not document.file:
            return Response({"detail": "No file is stored for this document."}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.name)
