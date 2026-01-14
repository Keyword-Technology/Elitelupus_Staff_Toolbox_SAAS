"""Tests for templates_manager app."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import SteamProfileSearch, SteamProfileBookmark
from .serializers import (
    SteamProfileBookmarkSerializer,
    SteamProfileBookmarkCreateSerializer,
    validate_tags_field
)

User = get_user_model()


class ValidateTagsFieldTestCase(TestCase):
    """Test case for the shared validate_tags_field function."""
    
    def test_filters_empty_strings(self):
        """Test that empty strings are filtered from tags array."""
        result = validate_tags_field(['', 'valid-tag', '', '  ', 'another-tag', ''])
        
        self.assertEqual(len(result), 2)
        self.assertIn('valid-tag', result)
        self.assertIn('another-tag', result)
        self.assertNotIn('', result)
        self.assertNotIn('  ', result)
    
    def test_trims_whitespace(self):
        """Test that tags are trimmed of leading/trailing whitespace."""
        result = validate_tags_field(['  tag1  ', ' tag2', 'tag3 '])
        
        self.assertEqual(result, ['tag1', 'tag2', 'tag3'])
    
    def test_handles_empty_list(self):
        """Test that empty list is handled correctly."""
        result = validate_tags_field([])
        
        self.assertEqual(result, [])
    
    def test_handles_none(self):
        """Test that None value is handled correctly."""
        result = validate_tags_field(None)
        
        self.assertEqual(result, [])
    
    def test_handles_all_empty(self):
        """Test that all empty strings returns empty list."""
        result = validate_tags_field(['', '  ', '', '   '])
        
        self.assertEqual(result, [])


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
        
        # Test the validate_tags method directly
        serializer = SteamProfileBookmarkSerializer(bookmark)
        validated_tags = serializer.validate_tags(['', 'valid-tag', '', '  ', 'another-tag', ''])
        
        self.assertEqual(len(validated_tags), 2)
        self.assertIn('valid-tag', validated_tags)
        self.assertIn('another-tag', validated_tags)
        self.assertNotIn('', validated_tags)
        self.assertNotIn('  ', validated_tags)


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
