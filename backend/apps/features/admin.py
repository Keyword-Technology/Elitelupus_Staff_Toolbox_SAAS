from django.contrib import admin
from .models import Feature, FeatureComment


class FeatureCommentInline(admin.TabularInline):
    model = FeatureComment
    extra = 0
    readonly_fields = ('author', 'created_at', 'updated_at')


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'created_by', 'created_at', 'comment_count')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    inlines = [FeatureCommentInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'


@admin.register(FeatureComment)
class FeatureCommentAdmin(admin.ModelAdmin):
    list_display = ('feature', 'author', 'content_preview', 'created_at')
    list_filter = ('created_at', 'feature')
    search_fields = ('content', 'author__username', 'feature__title')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
