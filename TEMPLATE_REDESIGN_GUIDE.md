# Steam Lookup & Template System Redesign - Implementation Guide

## What's Been Completed

### ✅ Backend Changes

1. **New Models Created** (`backend/apps/templates_manager/models.py`):
   - `BanExtensionTemplate` - Track ban extension requests with active ban detection
   - `PlayerReportTemplate` - Handle player reports (accepted/denied)
   - `StaffApplicationResponse` - Staff application reviews with ratings
   - `TemplateComment` - Comments/annotations on any template type

2. **Database Migrations**:
   - Generated and applied migration `0003_staff

applicationresponse_playerreporttemplate_and_more.py`
   - All new tables created successfully

3. **Admin Interface** (`backend/apps/templates_manager/admin.py`):
   - Admin classes added for all new models
   - Custom display methods (e.g., `is_active_ban`, `rating_stars`)

4. **Serializers** (`backend/apps/templates_manager/serializers.py`):
   - Created serializers for all new template types
   - Added `TemplateCommentSerializer` for comments

5. **Services Updated** (`backend/apps/templates_manager/services.py`):
   - Modified `SteamLookupService.lookup_profile()` to fetch ALL template types
   - Returns organized data: `related_templates: { refunds, ban_extensions, player_reports, staff_applications }`
   - Updated `_serialize_templates()` to handle multiple template types
   - Added debug logging for avatar URLs

6. **TypeScript Types** (`frontend/src/types/templates.ts`):
   - Complete type definitions for all template models
   - Updated `SteamProfile` interface with new structure

7. **API Client** (`frontend/src/lib/templateApi.ts`):
   - CRUD operations for all template types
   - Comment system API methods
   - Steam lookup function

### Frontend - Better Avatar Handling
- Added fallback to Steam's default avatar
- `onError` handler for failed image loads

---

## What Still Needs Implementation

### 1. Backend API Views & URLs

You need to create views and URL routes for the new templates:

**File: `backend/apps/templates_manager/views.py`**

Add these viewsets (similar to the existing `RefundTemplateViewSet`):

```python
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    BanExtensionTemplate, PlayerReportTemplate,
    StaffApplicationResponse, TemplateComment
)
from .serializers import (
    BanExtensionTemplateSerializer, PlayerReportTemplateSerializer,
    StaffApplicationResponseSerializer, TemplateCommentSerializer
)

class BanExtensionTemplateViewSet(viewsets.ModelViewSet):
    queryset = BanExtensionTemplate.objects.all()
    serializer_class = BanExtensionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter by steam_id_64 if provided
        steam_id = self.request.query_params.get('steam_id_64')
        if steam_id:
            qs = qs.filter(steam_id_64=steam_id)
        # Show active bans first
        return qs.order_by('-ban_expires_at', '-created_at')

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class PlayerReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = PlayerReportTemplate.objects.all()
    serializer_class = PlayerReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        steam_id = self.request.query_params.get('steam_id_64')
        if steam_id:
            qs = qs.filter(steam_id_64=steam_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(handled_by=self.request.user)


class StaffApplicationResponseViewSet(viewsets.ModelViewSet):
    queryset = StaffApplicationResponse.objects.all()
    serializer_class = StaffApplicationResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        steam_id = self.request.query_params.get('steam_id_64')
        if steam_id:
            qs = qs.filter(steam_id_64=steam_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(reviewed_by=self.request.user)


class TemplateCommentViewSet(viewsets.ModelViewSet):
    queryset = TemplateComment.objects.all()
    serializer_class = TemplateCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        template_type = self.request.query_params.get('template_type')
        template_id = self.request.query_params.get('template_id')
        
        if template_type and template_id:
            qs = qs.filter(template_type=template_type, template_id=template_id)
        
        return qs.order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

**File: `backend/apps/templates_manager/urls.py`**

Update URL patterns:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'refunds', views.RefundTemplateViewSet, basename='refund')
router.register(r'ban-extensions', views.BanExtensionTemplateViewSet, basename='ban-extension')
router.register(r'player-reports', views.PlayerReportTemplateViewSet, basename='player-report')
router.register(r'staff-applications', views.StaffApplicationResponseViewSet, basename='staff-application')
router.register(r'comments', views.TemplateCommentViewSet, basename='template-comment')

urlpatterns = [
    path('', include(router.urls)),
    path('steam-lookup/', views.SteamProfileLookupView.as_view(), name='steam-lookup'),
    # ... other existing paths
]
```

---

### 2. Frontend - Split Screen Layout

**File: `frontend/src/app/dashboard/templates/page.tsx`**

This is the main redesign - 2-column layout with Steam profile on left, templates on right:

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { templateAPI } from '@/lib/templateApi';
import { SteamProfile, Template } from '@/types/templates';
import toast from 'react-hot-toast';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import EnhancedSteamProfile from '@/components/templates/EnhancedSteamProfile';
import TemplatesPanel from '@/components/templates/TemplatesPanel';

export default function SteamLookupPage() {
  const { user } = useAuth();
  const [steamInput, setSteamInput] = useState('');
  const [lookingUp, setLookingUp] = useState(false);
  const [steamProfile, setSteamProfile] = useState<SteamProfile | null>(null);

  const handleSteamLookup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!steamInput.trim()) return;

    setLookingUp(true);
    try {
      const profile = await templateAPI.steamLookup(steamInput);
      setSteamProfile(profile);
      toast.success('Steam profile loaded');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to lookup Steam profile');
      console.error('Steam lookup error:', error);
    } finally {
      setLookingUp(false);
    }
  };

  const handleClear = () => {
    setSteamInput('');
    setSteamProfile(null);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Steam Lookup & Templates</h1>
        <p className="text-gray-400 mt-1">Search Steam profiles and manage templates</p>
      </div>

      {/* Steam Lookup Bar */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <form onSubmit={handleSteamLookup} className="flex gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={steamInput}
              onChange={(e) => setSteamInput(e.target.value)}
              placeholder="Enter Steam ID, Steam64, or STEAM_X:Y:Z format..."
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={lookingUp}
            />
          </div>
          <button
            type="submit"
            disabled={lookingUp || !steamInput.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
          >
            <MagnifyingGlassIcon className="w-5 h-5" />
            {lookingUp ? 'Looking up...' : 'Lookup'}
          </button>
          {steamProfile && (
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center gap-2 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
              Clear
            </button>
          )}
        </form>
      </div>

      {/* 2-Column Split Layout */}
      {steamProfile ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Steam Profile Details */}
          <div className="space-y-4">
            <EnhancedSteamProfile profile={steamProfile} />
          </div>

          {/* Right Column - Templates Panel */}
          <div className="space-y-4">
            <TemplatesPanel profile={steamProfile} />
          </div>
        </div>
      ) : (
        <div className="bg-dark-card rounded-lg border border-dark-border p-12 text-center">
          <MagnifyingGlassIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Enter a Steam ID to get started</p>
          <p className="text-gray-500 text-sm mt-2">
            Supports: Steam64, STEAM_X:Y:Z, or [U:1:XXXXX] formats
          </p>
        </div>
      )}
    </div>
  );
}
```

---

### 3. Templates Panel Component

**File: `frontend/src/components/templates/TemplatesPanel.tsx`**

```tsx
'use client';

import { useState, useMemo } from 'react';
import { SteamProfile, Template } from '@/types/templates';
import { MagnifyingGlassIcon, FunnelIcon, PlusIcon } from '@heroicons/react/24/outline';
import RefundTemplateCard from './RefundTemplateCard';
import BanExtensionCard from './BanExtensionCard';
import PlayerReportCard from './PlayerReportCard';
import StaffApplicationCard from './StaffApplicationCard';
import CreateTemplateModal from './CreateTemplateModal';

interface TemplatesPanelProps {
  profile: SteamProfile;
}

export default function TemplatesPanel({ profile }: TemplatesPanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Combine all templates with type information
  const allTemplates: Template[] = useMemo(() => {
    return [
      ...profile.related_templates.refunds.map(t => ({ ...t, type: 'refund' as const })),
      ...profile.related_templates.ban_extensions.map(t => ({ ...t, type: 'ban_extension' as const })),
      ...profile.related_templates.player_reports.map(t => ({ ...t, type: 'player_report' as const })),
      ...profile.related_templates.staff_applications.map(t => ({ ...t, type: 'staff_application' as const })),
    ];
  }, [profile]);

  // Sort: Active bans first, then by created_at desc
  const sortedTemplates = useMemo(() => {
    return [...allTemplates].sort((a, b) => {
      // Active bans first
      if (a.type === 'ban_extension' && b.type === 'ban_extension') {
        if (a.is_active_ban && !b.is_active_ban) return -1;
        if (!a.is_active_ban && b.is_active_ban) return 1;
      }
      // Then by date
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [allTemplates]);

  // Filter templates
  const filteredTemplates = useMemo(() => {
    let filtered = sortedTemplates;

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter(t => t.type === filterType);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(t => {
        const searchableText = JSON.stringify(t).toLowerCase();
        return searchableText.includes(term);
      });
    }

    return filtered;
  }, [sortedTemplates, filterType, searchTerm]);

  const templateCounts = {
    all: allTemplates.length,
    refund: profile.related_templates.refunds.length,
    ban_extension: profile.related_templates.ban_extensions.length,
    player_report: profile.related_templates.player_reports.length,
    staff_application: profile.related_templates.staff_applications.length,
  };

  return (
    <div className="bg-dark-card rounded-lg border border-dark-border p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Templates</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          New Template
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="space-y-3 mb-4">
        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {[
            { value: 'all', label: 'All' },
            { value: 'ban_extension', label: 'Ban Extensions' },
            { value: 'player_report', label: 'Reports' },
            { value: 'refund', label: 'Refunds' },
            { value: 'staff_application', label: 'Staff Apps' },
          ].map((filter) => (
            <button
              key={filter.value}
              onClick={() => setFilterType(filter.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                filterType === filter.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-bg text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {filter.label}
              <span className="ml-2 text-xs opacity-75">
                ({templateCounts[filter.value as keyof typeof templateCounts]})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Templates List */}
      <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto">
        {filteredTemplates.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FunnelIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No templates found</p>
          </div>
        ) : (
          filteredTemplates.map((template) => {
            switch (template.type) {
              case 'refund':
                return <RefundTemplateCard key={`refund-${template.id}`} template={template} />;
              case 'ban_extension':
                return <BanExtensionCard key={`ban-${template.id}`} template={template} />;
              case 'player_report':
                return <PlayerReportCard key={`report-${template.id}`} template={template} />;
              case 'staff_application':
                return <StaffApplicationCard key={`app-${template.id}`} template={template} />;
              default:
                return null;
            }
          })
        )}
      </div>

      {/* Create Template Modal */}
      {showCreateModal && (
        <CreateTemplateModal
          steamProfile={profile}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            // Refresh templates
          }}
        />
      )}
    </div>
  );
}
```

---

### 4. Individual Template Cards

You'll need to create card components for each template type. Example:

**File: `frontend/src/components/templates/BanExtensionCard.tsx`**

```tsx
'use client';

import { BanExtensionTemplate } from '@/types/templates';
import { formatDistanceToNow } from 'date-fns';
import { ClockIcon, DocumentDuplicateIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface BanExtensionCardProps {
  template: BanExtensionTemplate;
}

export default function BanExtensionCard({ template }: BanExtensionCardProps) {
  const copyToClipboard = () => {
    const text = `In-game Name: ${template.player_ign}
SteamID: ${template.steam_id}
Server number: ${template.server_number}
Ban Reason: ${template.ban_reason}
Current Ban Time: ${template.current_ban_time}
Required Ban Time: ${template.required_ban_time}
Reason For Extension: ${template.extension_reason}
Current Date: ${new Date().toLocaleDateString()}`;

    navigator.clipboard.writeText(text);
    toast.success('Ban extension copied to clipboard!');
  };

  const statusColors = {
    pending: 'bg-yellow-500',
    approved: 'bg-green-500',
    denied: 'bg-red-500',
  };

  return (
    <div className={`bg-dark-bg rounded-lg border p-4 ${
      template.is_active_ban ? 'border-red-500' : 'border-dark-border'
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-white font-semibold">{template.player_ign}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {formatDistanceToNow(new Date(template.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {template.is_active_ban && (
            <span className="px-2 py-1 bg-red-500 text-white text-xs font-medium rounded">
              ACTIVE BAN
            </span>
          )}
          <span className={`px-2 py-1 ${statusColors[template.status]} text-white text-xs font-medium rounded capitalize`}>
            {template.status}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-2 text-sm">
        <div className="text-gray-400">
          <span className="font-medium text-gray-300">Ban Reason:</span> {template.ban_reason}
        </div>
        <div className="flex gap-4 text-gray-400">
          <div>
            <span className="font-medium text-gray-300">Current:</span> {template.current_ban_time}
          </div>
          <div>
            <span className="font-medium text-gray-300">Required:</span> {template.required_ban_time}
          </div>
        </div>
        {template.ban_expires_at && (
          <div className="flex items-center gap-2 text-yellow-400">
            <ClockIcon className="w-4 h-4" />
            <span className="text-xs">
              Expires: {new Date(template.ban_expires_at).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-dark-border">
        <button
          onClick={copyToClipboard}
          className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded flex items-center justify-center gap-2 transition-colors"
        >
          <DocumentDuplicateIcon className="w-4 h-4" />
          Copy
        </button>
        <button className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors">
          <ChatBubbleLeftIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Submitted by */}
      <p className="text-xs text-gray-500 mt-2">
        Submitted by <span className="text-gray-400">{template.submitted_by}</span>
      </p>
    </div>
  );
}
```

---

## Next Steps

1. **Create remaining viewsets** in `backend/apps/templates_manager/views.py`
2. **Update URL routes** in `backend/apps/templates_manager/urls.py`
3. **Create template card components** for each type (Refund, Player Report, Staff App)
4. **Create the TemplatesPanel** component
5. **Update the templates page** with the new 2-column layout
6. **Create template forms** for creating new templates
7. **Add comments UI** to template cards
8. **Test the entire flow** end-to-end

The backend foundation is complete. The main work remaining is frontend UI components!
