import base64
import io
import logging
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from PIL import Image
from rest_framework import serializers
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer
from users.serializers import UserDisplaySerializer

from responses.models import Response, ResponseImage

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024  # 2 Mo par image


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",
            "data",
            "context",
            "status",
        )
        read_only_fields = ("id", "status", "respondant")

    def create(self, validated_data):
        data = validated_data.get("data", {})
        schema = validated_data["survey"].json_schema or {}

        with transaction.atomic():
            response = Response.objects.create(**validated_data)
            ResponseSerializer._create_images_from_data(response, data, schema)

        return response

    @staticmethod
    def _create_images_from_data(response, data, schema):
        modified = False
        for field in schema.get("fields", []):
            if field.get("ui", {}).get("widget") != "image":
                continue
            field_id = field["id"]
            images = data.get(field_id, [])
            if not isinstance(images, list):
                continue

            processed = []
            for item in images:
                if not isinstance(item, dict):
                    continue
                try:
                    serializer = ResponseImageSerializer(data=item)
                    serializer.is_valid(raise_exception=True)
                    img_obj = serializer.save(response=response)
                    processed.append({"id": img_obj.id})
                except serializers.ValidationError:
                    raise
                except Exception:
                    logger.warning("Failed to process image for field %s", field_id, exc_info=True)
                    continue

            data[field_id] = processed
            modified = True

        if modified:
            response.data = data
            response.save(update_fields=["data"])


class ResponseDisplaySerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = SurveyDisplaySerializer(read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",
            "status",
            "creation_date",
        )
        read_only_fields = fields


class FullResponseSerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = FullSurveySerializer(read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",
            "data",
            "context",
            "status",
            "creation_date",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        schema = instance.survey.json_schema or {}
        image_field_ids = [f["id"] for f in schema.get("fields", []) if f.get("ui", {}).get("widget") == "image"]
        if not image_field_ids:
            return ret

        images_by_id = {img.id: img for img in instance.images.all()}
        data = ret.get("data") or {}

        for field_id in image_field_ids:
            items = data.get(field_id)
            if not isinstance(items, list):
                continue
            enriched = []
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    img = images_by_id.get(item["id"])
                    if img:
                        enriched.append(ResponseImageSerializer(img).data)
                else:
                    enriched.append(item)
            data[field_id] = enriched

        ret["data"] = data
        return ret


def get_base_url() -> str:
    scheme = "https" if settings.SECURE else "http"
    return f"{scheme}://{settings.HOSTNAME}/"


class ResponseImageSerializer(serializers.ModelSerializer):
    file = serializers.CharField(write_only=True)
    thumbnail = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ResponseImage
        fields = ("id", "file", "thumbnail", "file_url")

    def get_thumbnail(self, obj):
        if not obj.thumbnail:
            return None
        with obj.thumbnail.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def get_file_url(self, obj):
        url = obj.file.url
        if url.startswith("http"):
            return url
        return get_base_url().rstrip("/") + url

    def validate_file(self, value):
        if len(value) > int(MAX_IMAGE_SIZE_BYTES * 4 / 3):
            raise serializers.ValidationError("Image trop volumineuse (max 2 Mo).")
        try:
            base64.b64decode(value, validate=True)
        except Exception:
            raise serializers.ValidationError("Données d'image invalides.")
        return value

    def create(self, validated_data):
        b64_string = validated_data.pop("file")
        image_data = base64.b64decode(b64_string)
        response = validated_data["response"]
        uid = uuid.uuid4().hex[:8]

        img = Image.open(io.BytesIO(image_data))
        thumb = img.copy()
        if thumb.mode in ("RGBA", "P"):
            thumb = thumb.convert("RGB")
        thumb.thumbnail((200, 200), Image.LANCZOS)
        thumb_io = io.BytesIO()
        thumb.save(thumb_io, format="JPEG", quality=60)
        thumb_io.seek(0)

        return ResponseImage.objects.create(
            **validated_data,
            file=ContentFile(image_data, name=f"{response.id}_{uid}.jpg"),
            thumbnail=ContentFile(thumb_io.read(), name=f"{response.id}_{uid}_thumb.jpg"),
        )
