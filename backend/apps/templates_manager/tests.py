"""Tests for templates_manager app."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import SteamProfileSearch, SteamProfileBookmark
from .serializers import SteamProfileBookmarkSerializer, SteamProfileBookmarkCreateSerializer

User = get_user_model()


class SteamProfileBookmarkSerializerTestCase(TestCase):
    """Test case for SteamProfileBookmark serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.steam_profile = SteamProfileSearch.objects.create(
            steam_id_64='76561199012665547',
            steam_id='STEAM_0:1:526199909',
            persona_name='TestPlayer'
        )
    
    def test_validate_tags_filters_empty_strings(self):
        """Test that empty strings are filtered from tags array."""
        # Create bookmark with empty tags
        bookmark = SteamProfileBookmark.objects.create(
            user=self.user,
            steam_profile=self.steam_profile,
            tags=['', 'valid-tag', '', '  ', 'another-tag', '']
        )
        
        # Serialize the bookmark
        serializer = SteamProfileBookmarkSerializer(bookmark)
        
        # Verify empty tags are not in the serialized data
        # Note: The validation happens on update/create, not on read
        # So we need to test the validate_tags method directly
        validated_tags = serializer.validate_tags(['', 'valid-tag', '', '  ', 'another-tag', ''])
        
        self.assertEqual(len(validated_tags), 2)
        self.assertIn('valid-tag', validated_tags)
        self.assertIn('another-tag', validated_tags)
        self.assertNotIn('', validated_tags)
        self.assertNotIn('  ', validated_tags)
    
    def test_validate_tags_trims_whitespace(self):
        """Test that tags are trimmed of leading/trailing whitespace."""
        serializer = SteamProfileBookmarkSerializer()
        
        validated_tags = serializer.validate_tags(['  tag1  ', ' tag2', 'tag3 '])
        
        self.assertEqual(validated_tags, ['tag1', 'tag2', 'tag3'])
    
    def test_validate_tags_handles_empty_list(self):
        """Test that empty list is handled correctly."""
        serializer = SteamProfileBookmarkSerializer()
        
        validated_tags = serializer.validate_tags([])
        
        self.assertEqual(validated_tags, [])
    
    def test_validate_tags_handles_none(self):
        """Test that None value is handled correctly."""
        serializer = SteamProfileBookmarkSerializer()
        
        validated_tags = serializer.validate_tags(None)
        
        self.assertEqual(validated_tags, [])
    
    def test_validate_tags_handles_all_empty(self):
        """Test that all empty strings returns empty list."""
        serializer = SteamProfileBookmarkSerializer()
        
        validated_tags = serializer.validate_tags(['', '  ', '', '   '])
        
        self.assertEqual(validated_tags, [])


class SteamProfileBookmarkCreateSerializerTestCase(TestCase):
    """Test case for SteamProfileBookmarkCreateSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_validate_tags_in_create_serializer(self):
        """Test that tag validation works in create serializer."""
        serializer = SteamProfileBookmarkCreateSerializer()
        
        validated_tags = serializer.validate_tags(['', 'tag1', '', 'tag2', '  '])
        
        self.assertEqual(len(validated_tags), 2)
        self.assertIn('tag1', validated_tags)
        self.assertIn('tag2', validated_tags)
