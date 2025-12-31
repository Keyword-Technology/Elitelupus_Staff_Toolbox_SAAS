# Template Search, Filter & Creation Wizard Implementation

## Overview
Enhanced the Templates page with advanced search, filtering, and a multi-step wizard for creating structured templates.

## Features Implemented

### 1. Template Search Bar
- **Location**: Under the "Templates" column header
- **Functionality**: Real-time search across template names and content
- **UI**: Search input with magnifying glass icon
- **State**: `templateSearchTerm` tracks the search query

### 2. Filter Buttons
- **Types**: 
  - All (default)
  - Refund
  - Ban
  - Report
  - Application
- **Display**: Shows count of templates in each category
- **Active State**: Highlighted with primary color when selected
- **State**: `templateFilter` tracks the active filter

### 3. Filtered Template List
- **Logic**: Combines search term and filter using `filteredTemplates` computation
- **Empty State**: 
  - Shows "No templates match your search criteria" when filtered
  - Shows "No templates yet" when no templates exist
- **Display**: Same card-based layout with selection and deletion

### 4. Template Creation Wizard Modal
- **Trigger**: "Create New" button with plus icon
- **Steps**: 2-step process

#### Step 1: Template Type Selection
Four template type options displayed in a 2x2 grid:
1. **Refund Template** 💰 - Process item refunds
2. **Ban Extension** 🔨 - Extend player bans
3. **Player Report** 📝 - Report rule violations
4. **Staff Application** 👮 - Review staff apps

**UI**: Large clickable cards with emoji icons, labels, and descriptions

#### Step 2: Form Fields
Dynamic form fields based on selected template type:

##### Refund Template Fields:
- Player IGN (auto-filled from Steam profile if available)
- SteamID64 (auto-filled from Steam profile if available)
- Server (dropdown: Server 1, Server 2)
- Items Lost (textarea)
- Reason (textarea)
- Proof URL (text input)

##### Ban Extension Template Fields:
- Player IGN (auto-filled from Steam profile)
- SteamID (auto-filled from Steam profile)
- Server (dropdown)
- Ban Reason (text input)
- Current Ban Time (text input, e.g., "1 week")
- Required Ban Time (text input, e.g., "2 weeks")
- Extension Reason (textarea)

##### Player Report Template Fields:
- Reported Player IGN (text input)
- SteamID64 (text input)
- Violation Type (dropdown: RDM, LTAP, FailRP, Propblock, Harassment, Other)
- Server (dropdown)
- Description (textarea)
- Evidence URLs (textarea, one per line)

##### Staff Application Template Fields:
- Applicant Name (text input)
- SteamID64 (text input)
- Position Applied For (dropdown: T-Staff, Operator, Moderator)
- Review Status (dropdown: Pending, Interview, Approved, Denied)
- Reviewer Notes (textarea)
- Experience Level (dropdown: None, Some, Moderate, Experienced)

## State Management

### New State Variables:
```typescript
const [showWizardModal, setShowWizardModal] = useState(false);
const [wizardStep, setWizardStep] = useState(1);
const [selectedTemplateType, setSelectedTemplateType] = useState('');
const [templateSearchTerm, setTemplateSearchTerm] = useState('');
const [templateFilter, setTemplateFilter] = useState('all');
const [wizardData, setWizardData] = useState<any>({});
```

### Handler Functions:
- `handleStartWizard()`: Opens wizard modal at step 1
- `handleWizardNext()`: Advances to form fields (step 2)
- `handleWizardSubmit()`: Submits the filled template data
- `filteredTemplates`: Computed value filtering templates by search and filter

## Steam Profile Integration
When a Steam profile is looked up, the wizard automatically pre-fills:
- Player IGN → from `steamProfile.profile.name`
- SteamID → from `steamProfile.steam_id`
- SteamID64 → from `steamProfile.steam_id_64`

## UI/UX Improvements

### Layout:
- Split-screen 2-column grid (Lookup left, Templates right)
- Templates column has sticky header with "Create New" button
- Search bar is full-width with icon
- Filter buttons wrap nicely on smaller screens
- Wizard modal is centered with max-width constraint

### Styling:
- Dark theme consistency
- Primary color highlights for active states
- Smooth transitions on hover/click
- Clear visual hierarchy with spacing
- Responsive design for various screen sizes

### User Flow:
1. User clicks "Create New" in Templates column
2. Wizard modal opens showing 4 template type options
3. User selects a template type (card highlights)
4. User clicks "Next" → advances to step 2
5. Form displays relevant fields for selected type
6. Fields auto-populate if Steam profile is available
7. User fills remaining fields
8. User clicks "Submit Template" → API call made
9. Success toast shown, modal closes, template list refreshes

## Backend Integration
- Wizard calls `templateAPI.createRefund()` for refund templates
- Other template types ready for API implementation
- Error handling with toast notifications
- Automatic template list refresh after creation

## Next Steps (Future Enhancements)
1. Implement backend APIs for other template types (Ban Extension, Player Report, Staff Application)
2. Add template preview before submission
3. Add form validation with error messages
4. Add "Save as Draft" functionality
5. Add template editing wizard (similar flow)
6. Add template duplication feature
7. Add export/import templates functionality

## File Modified
- `frontend/src/app/dashboard/templates/page.tsx` - Main templates page component

## Dependencies
- `@heroicons/react/24/outline` - Icons (MagnifyingGlassIcon, PlusIcon, etc.)
- `react-hot-toast` - Toast notifications
- `@/lib/api` - API client (templateAPI)
- `@/components/templates/EnhancedSteamProfile` - Steam profile display component

## Testing Checklist
- [ ] Search bar filters templates correctly
- [ ] Filter buttons show accurate counts
- [ ] Clicking filter buttons updates template list
- [ ] "Create New" button opens wizard modal
- [ ] Template type selection works (cards highlight)
- [ ] "Next" button disabled until type selected
- [ ] "Back" button returns to step 1
- [ ] Form fields display correctly for each type
- [ ] Steam profile data auto-fills when available
- [ ] Submit creates template successfully
- [ ] Error handling shows appropriate messages
- [ ] Modal closes after successful submission
- [ ] Template list refreshes after creation
