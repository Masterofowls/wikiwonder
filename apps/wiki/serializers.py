from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.wiki.models import Bookmark, Category, Tag, WikiPage, WikiSection


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class WikiSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiSection
        fields = ["id", "title", "slug", "content", "order", "anchor"]


class WikiPageListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = WikiPage
        fields = [
            "id", "title", "slug", "summary", "status", "category", "category_name",
            "is_featured", "view_count", "author_name", "created_at", "updated_at",
        ]


class WikiPageDetailSerializer(serializers.ModelSerializer):
    sections = WikiSectionSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = WikiPage
        fields = [
            "id", "title", "slug", "summary", "content", "status", "category",
            "tags", "sections", "is_featured", "view_count", "created_at", "updated_at",
        ]


class WikiPageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = WikiPage.objects.select_related("category", "author").prefetch_related(
            "sections", "tags"
        )
        if not self.request.user.is_staff:
            qs = qs.filter(status=WikiPage.Status.PUBLISHED)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return WikiPageDetailSerializer
        return WikiPageListSerializer

    @action(detail=True, methods=["get"])
    def preview(self, request, slug=None):
        page = self.get_object()
        return Response({"title": page.title, "summary": page.summary, "slug": page.slug})


class BookmarkSerializer(serializers.ModelSerializer):
    page_title = serializers.CharField(source="page.title", read_only=True)
    page_slug = serializers.CharField(source="page.slug", read_only=True)

    class Meta:
        model = Bookmark
        fields = ["id", "page", "page_title", "page_slug", "note", "created_at"]
        read_only_fields = ["user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Bookmark.objects.filter(user=self.request.user).select_related("page")
        return Bookmark.objects.none()
