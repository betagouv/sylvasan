import base64
import io
import logging
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from djangorestframework_camel_case.util import camelize
from PIL import Image
from rest_framework import serializers
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer
from surveys.serializers.surveyfollowup import SurveyFollowUpSerializer
from users.serializers import UserDisplaySerializer

from responses.models import Response, ResponseImage

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024  # 2 Mo par image


def get_base_url() -> str:
    scheme = "https" if settings.SECURE else "http"
    return f"{scheme}://{settings.HOSTNAME}/"


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
    def _process_images(response, data, fields):
        # Modifie `data` in-place. Retourne True si des modifications ont été effectuées.
        modified = False
        for field in fields:
            field_id = field["id"]
            widget = field.get("ui", {}).get("widget")

            if widget == "image":
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

            elif field.get("type") == "array" and field.get("fields"):
                items = data.get(field_id)
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if ResponseSerializer._process_images(response, item, field["fields"]):
                        modified = True

        return modified

    @staticmethod
    def _create_images_from_data(response, data, schema):
        # Notez que cette fonction modifie "data" in-place, après que l'objet Response
        # est créé. C'est intentionnel mais pas très propre.
        modified = ResponseSerializer._process_images(response, data, schema.get("fields", []))
        if modified:
            response.data = data
            response.save(update_fields=["data"])


class FollowUpResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = (
            "id",
            "survey_follow_up",
            "parent_response",
            "respondant",
            "data",
            "context",
            "status",
        )
        read_only_fields = ("id", "status", "respondant")

    def validate(self, data):
        if not data.get("parent_response"):
            raise serializers.ValidationError(
                {"parent_response": "Ce champ est obligatoire pour une réponse de suivi."}
            )
        follow_up = data.get("survey_follow_up")
        parent = data.get("parent_response")
        if follow_up and parent and parent.survey_id != follow_up.parent_survey_id:
            raise serializers.ValidationError(
                {"parent_response": "La réponse parente doit appartenir à l'enquête parente du suivi."}
            )
        return data

    def create(self, validated_data):
        data = validated_data.get("data", {})
        schema = validated_data["survey_follow_up"].json_schema or {}

        with transaction.atomic():
            response = Response.objects.create(**validated_data)
            ResponseSerializer._create_images_from_data(response, data, schema)

        return response


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


def _resolve_images(data, fields, images_by_id, image_serializer_class):
    for field in fields:
        field_id = field["id"]
        widget = field.get("ui", {}).get("widget")

        if widget == "image":
            items = data.get(field_id)
            if not isinstance(items, list):
                continue
            data[field_id] = [
                camelize(image_serializer_class(images_by_id[item["id"]]).data)
                if isinstance(item, dict) and "id" in item and item["id"] in images_by_id
                else item
                for item in items
            ]

        elif field.get("type") == "array" and field.get("fields"):
            items = data.get(field_id)
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    _resolve_images(item, field["fields"], images_by_id, image_serializer_class)


def _enrich_image_fields(ret, instance, image_serializer_class):
    source = instance.survey or instance.survey_follow_up
    schema = (source.json_schema if source else None) or {}
    fields = schema.get("fields", [])
    if not fields:
        return ret

    images_by_id = {img.id: img for img in instance.images.all()}
    data = ret.get("data") or {}
    _resolve_images(data, fields, images_by_id, image_serializer_class)
    ret["data"] = data
    return ret


class FullResponseSerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = FullSurveySerializer(read_only=True)
    survey_follow_up = SurveyFollowUpSerializer(read_only=True)
    parent_response = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "survey_follow_up",
            "parent_response",
            "respondant",
            "data",
            "context",
            "status",
            "creation_date",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        return _enrich_image_fields(super().to_representation(instance), instance, ResponseImageSerializer)


class FullResponseSerializerWithFollowUps(FullResponseSerializer):
    follow_up_responses = FullResponseSerializer(many=True, read_only=True)

    class Meta(FullResponseSerializer.Meta):
        fields = FullResponseSerializer.Meta.fields + ("follow_up_responses",)
        read_only_fields = fields


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


class ResponseImageExportSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ResponseImage
        fields = ("id", "file_url")

    def get_file_url(self, obj):
        url = obj.file.url
        if url.startswith("http"):
            return url
        return get_base_url().rstrip("/") + url


class ResponseExportSerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = serializers.PrimaryKeyRelatedField(read_only=True)

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
        return _enrich_image_fields(super().to_representation(instance), instance, ResponseImageExportSerializer)
