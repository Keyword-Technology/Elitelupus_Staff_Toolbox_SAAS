// Template Types

export interface RefundTemplate {
  id: number;
  type: 'refund';
  ticket_number: string;
  status: 'pending' | 'approved' | 'denied' | 'completed';
  player_ign: string;
  steam_id: string;
  steam_id_64: string;
  server: 'OG' | 'Normal';
  items_lost: string;
  reason: string;
  evidence?: string;
  refund_amount?: string;
  admin_notes?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BanExtensionTemplate {
  id: number;
  type: 'ban_extension';
  player_ign: string;
  steam_id: string;
  steam_id_64: string;
  server_number: string;
  ban_reason: string;
  current_ban_time: string;
  required_ban_time: string;
  extension_reason: string;
  status: 'pending' | 'approved' | 'denied';
  is_active_ban: boolean;
  ban_expires_at?: string;
  submitted_by: string;
  approved_by?: string;
  admin_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PlayerReportTemplate {
  id: number;
  type: 'player_report';
  player_ign: string;
  steam_id: string;
  steam_id_64: string;
  case_link: string;
  report_reason: string;
  evidence_provided?: string;
  status: 'pending' | 'accepted' | 'denied';
  decision_reason: string;
  action_taken: 'none' | 'warned' | 'banned' | 'kicked';
  handled_by: string;
  created_at: string;
  updated_at: string;
}

export interface StaffApplicationResponse {
  id: number;
  type: 'staff_application';
  applicant_name: string;
  steam_id_64?: string;
  discord_username?: string;
  positive_rep: string;
  neutral_rep?: string;
  negative_rep?: string;
  overall_comment: string;
  rating: 1 | 2 | 3 | 4 | 5;
  rating_stars: string;
  recommend_hire: boolean;
  recommended_role?: string;
  reviewed_by: string;
  created_at: string;
  updated_at: string;
}

export type Template = 
  | RefundTemplate 
  | BanExtensionTemplate 
  | PlayerReportTemplate 
  | StaffApplicationResponse;

export interface TemplateComment {
  id: number;
  author: string;
  author_name: string;
  template_type: 'refund' | 'ban_extension' | 'player_report' | 'staff_application';
  template_id: number;
  comment: string;
  created_at: string;
  updated_at: string;
}

export interface SteamProfile {
  id?: number;
  steam_id: string;
  steam_id_64: string;
  profile: {
    name: string;
    account_name?: string;
    profile_url: string;
    avatar_url: string;
    profile_state: string;
    real_name?: string;
    
    // Steam IDs
    steam_id_3?: string;
    custom_url?: string;
    
    // Status
    persona_state: number;
    persona_state_text: string;
    last_logoff?: string;
    
    // Location
    location?: string;
    country_code?: string;
    state_code?: string;
    
    // Game info
    game_id?: string;
    game_extra_info?: string;
    game_server_ip?: string;
    
    // Account details
    is_private: boolean;
    is_limited: boolean;
    level?: number;
    account_created?: string;
    comment_permission: boolean;
    
    // Enhanced scraped data from steamid.pro
    vanity_url?: string;
    account_id?: string;
    steam_id_2?: string;
    invite_url?: string;
    invite_url_short?: string;
    fivem_hex?: string;
    online_status?: string;
    estimated_value?: string;
    rating_value?: number;
    rating_count?: number;
    scraped_description?: string;
    last_scraped_at?: string;
    past_names?: Array<{name: string; first_seen: string; last_seen: string}>;
  };
  bans: {
    vac_bans: number;
    game_bans: number;
    days_since_last_ban?: number;
    vac_ban_dates?: string[];
    community_banned: boolean;
    trade_ban: string;
  };
  search_stats: {
    total_searches: number;
    first_searched: string;
    last_searched: string;
    last_searched_by?: string;
  };
  changes: Record<string, any>;
  related_templates: {
    refunds: RefundTemplate[];
    ban_extensions: BanExtensionTemplate[];
    player_reports: PlayerReportTemplate[];
    staff_applications: StaffApplicationResponse[];
  };
  search_history: Array<{
    searched_at: string;
    searched_by: string;
    persona_name: string;
    vac_bans: number;
    game_bans: number;
    changes: Record<string, any>;
  }>;
}

// Steam Profile Notes
export interface SteamProfileNote {
  id: number;
  steam_profile: number;
  author: number;
  author_name: string;
  author_role: string;
  note_type: 'general' | 'warning_verbal' | 'behavior';
  note_type_display: string;
  title?: string;
  content: string;
  is_active: boolean;
  severity: 1 | 2 | 3 | 4;
  severity_display: string;
  server?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolved_by?: number;
  resolved_by_name?: string;
  warning_count: number;
}

// Steam Profile Bookmarks
export interface SteamProfileBookmark {
  id: number;
  user: number;
  user_name: string;
  steam_profile: number;
  steam_profile_data: {
    steam_id_64: string;
    persona_name: string;
    avatar_url: string;
    profile_url: string;
    vac_bans: number;
    game_bans: number;
    last_searched_at: string;
    search_count: number;
  };
  note?: string;
  tags: string[];
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

