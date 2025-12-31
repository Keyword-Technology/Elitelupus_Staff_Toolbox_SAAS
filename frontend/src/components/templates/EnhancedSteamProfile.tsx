import { 
  ExclamationTriangleIcon, 
  ShieldCheckIcon,
  ClockIcon,
  UserIcon,
  GlobeAltIcon,
  CalendarIcon,
  EyeIcon,
  EyeSlashIcon,
  DocumentTextIcon,
  ClipboardDocumentIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow, format } from 'date-fns';
import toast from 'react-hot-toast';

interface SteamProfileData {
  steam_id: string;
  steam_id_64: string;
  profile: {
    name: string;
    account_name?: string;
    profile_url: string;
    avatar_url: string;
    profile_state: string;
    real_name?: string;
    location?: string;
    is_private: boolean;
    is_limited: boolean;
    level?: number;
    account_created?: string;
    persona_state?: number;
    persona_state_text?: string;
    steam_id_3?: string;
    steam_id_2?: string;
    custom_url?: string;
    vanity_url?: string;
    account_id?: string;
    country_code?: string;
    state_code?: string;
    game_extra_info?: string;
    comment_permission?: boolean;
    last_logoff?: string;
    // Enhanced scraped data
    fivem_hex?: string;
    invite_url?: string;
    invite_url_short?: string;
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
    community_banned: boolean;
    trade_ban: string;
  };
  search_stats: {
    total_searches: number;
    first_searched: string;
    last_searched: string;
    last_searched_by?: string;
  };
  changes: Record<string, { old: any; new: any }>;
  related_templates: Array<{
    id: number;
    ticket_number: string;
    status: string;
    player_ign: string;
    created_by: string;
    created_at: string;
    items_lost: string;
  }>;
  search_history: Array<{
    searched_at: string;
    searched_by: string;
    persona_name: string;
    vac_bans: number;
    game_bans: number;
    changes: Record<string, any>;
  }>;
}

interface Props {
  profile: SteamProfileData;
}

export default function EnhancedSteamProfile({ profile }: Props) {
  const hasVACBan = profile.bans.vac_bans > 0;
  const hasGameBan = profile.bans.game_bans > 0;
  const hasCommunityBan = profile.bans.community_banned;
  const hasTradeBan = profile.bans.trade_ban && profile.bans.trade_ban !== 'none';
  const hasAnyBan = hasVACBan || hasGameBan || hasCommunityBan || hasTradeBan;

  const hasRecentChanges = Object.keys(profile.changes).length > 0;

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  };

  return (
    <div className="space-y-6">
      {/* Quick Actions Bar */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => copyToClipboard(profile.steam_id, 'Steam ID')}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <ClipboardDocumentIcon className="w-4 h-4" />
            Copy Steam ID
          </button>
          <button
            onClick={() => copyToClipboard(profile.steam_id_64, 'Steam64')}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <ClipboardDocumentIcon className="w-4 h-4" />
            Copy Steam64
          </button>
          <a
            href={profile.profile.profile_url || `https://steamcommunity.com/profiles/${profile.steam_id_64}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            Open Steam Profile
          </a>
          <a
            href={`https://steamid.io/lookup/${profile.steam_id_64}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            View on SteamID.io
          </a>
          <a
            href={`https://steamid.pro/lookup/${profile.steam_id_64}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            View on SteamID.pro
          </a>
        </div>
      </div>

      {/* Header with Avatar and Basic Info */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <div className="flex items-start gap-6">
          <img
            src={profile.profile.avatar_url && profile.profile.avatar_url.trim() !== '' 
              ? profile.profile.avatar_url 
              : 'https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'}
            alt={profile.profile.name || 'Steam Profile'}
            className="w-24 h-24 rounded-lg"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = 'https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg';
            }}
          />
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                  {profile.profile.name}
                  {profile.profile.is_private && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded">
                      <EyeSlashIcon className="w-3 h-3" />
                      Private
                    </span>
                  )}
                  {profile.profile.is_limited && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-yellow-900/50 text-yellow-400 rounded">
                      Limited Account
                    </span>
                  )}
                </h2>
                {profile.profile.real_name && (
                  <p className="text-gray-400 mt-1">{profile.profile.real_name}</p>
                )}
                
                {/* Status */}
                <div className="flex items-center gap-2 mt-2">
                  <div className={`w-2 h-2 rounded-full ${
                    profile.profile.persona_state === 1 ? 'bg-green-500' : 
                    profile.profile.persona_state === 0 ? 'bg-gray-500' : 
                    'bg-yellow-500'
                  }`} />
                  <span className="text-sm text-gray-400">
                    {profile.profile.persona_state_text || 'Unknown'}
                  </span>
                  {profile.profile.game_extra_info && (
                    <span className="text-sm text-green-400">
                      Playing {profile.profile.game_extra_info}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Steam IDs Section */}
            <div className="mt-4 p-3 bg-dark-bg rounded border border-dark-border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-400">steamID:</span>{' '}
                  <span className="text-white font-mono">{profile.steam_id}</span>
                </div>
                {profile.profile.steam_id_2 && (
                  <div>
                    <span className="text-gray-400">steamID2:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.steam_id_2}</span>
                  </div>
                )}
                {profile.profile.steam_id_3 && (
                  <div>
                    <span className="text-gray-400">steamID3:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.steam_id_3}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-400">steamID64:</span>{' '}
                  <span className="text-white font-mono">{profile.steam_id_64}</span>
                </div>
                {profile.profile.account_id && (
                  <div>
                    <span className="text-gray-400">Account ID:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.account_id}</span>
                  </div>
                )}
                {profile.profile.vanity_url && (
                  <div>
                    <span className="text-gray-400">Vanity URL:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.vanity_url}</span>
                  </div>
                )}
                {profile.profile.custom_url && (
                  <div>
                    <span className="text-gray-400">Custom URL:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.custom_url}</span>
                  </div>
                )}
                {profile.profile.fivem_hex && (
                  <div>
                    <span className="text-gray-400">FiveM HEX:</span>{' '}
                    <span className="text-white font-mono">{profile.profile.fivem_hex}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Profile Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4 text-sm">
              <div>
                <p className="text-gray-400">profile state</p>
                <p className="text-white capitalize">{profile.profile.profile_state || 'Unknown'}</p>
              </div>
              
              {profile.profile.account_created && (
                <div>
                  <p className="text-gray-400">profile created</p>
                  <p className="text-white">
                    {format(new Date(profile.profile.account_created), 'MMMM d, yyyy')}
                  </p>
                </div>
              )}
              
              <div>
                <p className="text-gray-400">name</p>
                <p className="text-white">{profile.profile.name || 'Unknown'}</p>
              </div>
              
              {profile.profile.account_name && (
                <div>
                  <p className="text-gray-400">account name</p>
                  <p className="text-white font-mono">{profile.profile.account_name}</p>
                </div>
              )}
              
              {profile.profile.real_name && (
                <div>
                  <p className="text-gray-400">real name</p>
                  <p className="text-white">{profile.profile.real_name}</p>
                </div>
              )}
              
              <div>
                <p className="text-gray-400">location</p>
                <p className="text-white">
                  {profile.profile.location || 
                   (profile.profile.country_code && profile.profile.state_code 
                     ? `${profile.profile.state_code}, ${profile.profile.country_code}` 
                     : profile.profile.country_code || 'not set')}
                </p>
              </div>
              
              <div>
                <p className="text-gray-400">status</p>
                <p className="text-white">{profile.profile.persona_state_text?.toLowerCase() || 'unknown'}</p>
              </div>
              
              {profile.profile.last_logoff && (
                <div>
                  <p className="text-gray-400">last online</p>
                  <p className="text-white">
                    {formatDistanceToNow(new Date(profile.profile.last_logoff), { addSuffix: true })}
                  </p>
                </div>
              )}
              
              {profile.profile.level && (
                <div>
                  <p className="text-gray-400">level</p>
                  <p className="text-white font-semibold">{profile.profile.level}</p>
                </div>
              )}
              
              <div>
                <p className="text-gray-400">comments</p>
                <p className="text-white">{profile.profile.comment_permission ? 'enabled' : 'disabled'}</p>
              </div>
              
              {profile.profile.online_status && (
                <div>
                  <p className="text-gray-400">online status</p>
                  <p className="text-white">{profile.profile.online_status}</p>
                </div>
              )}
              
              {profile.profile.estimated_value && (
                <div>
                  <p className="text-gray-400">estimated value</p>
                  <p className="text-white font-semibold text-green-400">${profile.profile.estimated_value}</p>
                </div>
              )}
              
              {(profile.profile.rating_value != null || profile.profile.rating_count != null) && (
                <div>
                  <p className="text-gray-400">community rating</p>
                  <p className="text-white">
                    ⭐ {profile.profile.rating_value?.toFixed(2) || '0'}/5.0 
                    <span className="text-gray-400 text-xs ml-1">({profile.profile.rating_count || 0} votes)</span>
                  </p>
                </div>
              )}
              
              {profile.profile.invite_url_short && (
                <div className="col-span-2">
                  <p className="text-gray-400">invite link</p>
                  <a 
                    href={profile.profile.invite_url_short} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 font-mono text-xs truncate block"
                  >
                    {profile.profile.invite_url_short}
                  </a>
                </div>
              )}
            </div>

            {/* Past IGN Names */}
            {profile.profile.past_names && profile.profile.past_names.length > 0 && (
              <div className="mt-4 p-3 bg-dark-bg rounded-lg border border-dark-border">
                <p className="text-gray-400 text-sm mb-2 flex items-center gap-2">
                  <ClockIcon className="w-4 h-4" />
                  Past Names ({profile.profile.past_names.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {profile.profile.past_names
                    .slice(0, 20)
                    .map((entry, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
                        title={`First seen: ${formatDistanceToNow(new Date(entry.first_seen))} ago\nLast seen: ${formatDistanceToNow(new Date(entry.last_seen))} ago`}
                      >
                        {entry.name}
                      </span>
                    ))}
                  {profile.profile.past_names.length > 20 && (
                    <span className="px-2 py-1 text-gray-500 text-xs">
                      +{profile.profile.past_names.length - 20} more
                    </span>
                  )}
                  {profile.profile.past_names.length === 0 && (
                    <span className="text-gray-500 text-xs">No name history available</span>
                  )}
                </div>
              </div>
            )}

            <a
              href={profile.profile.profile_url || `https://steamcommunity.com/profiles/${profile.steam_id_64}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors"
            >
              <ArrowTopRightOnSquareIcon className="w-4 h-4" />
              View Steam Profile
            </a>
          </div>
        </div>
      </div>

      {/* Bans and Restrictions */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          {hasAnyBan ? (
            <>
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
              Bans & Restrictions
            </>
          ) : (
            <>
              <ShieldCheckIcon className="w-5 h-5 text-green-400" />
              Account Status
            </>
          )}
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className={`p-4 rounded-lg ${hasVACBan ? 'bg-red-900/20 border border-red-500/50' : 'bg-dark-bg'}`}>
            <p className="text-gray-400 text-sm">VAC Bans</p>
            <p className={`text-2xl font-bold ${hasVACBan ? 'text-red-400' : 'text-green-400'}`}>
              {profile.bans.vac_bans}
            </p>
          </div>

          <div className={`p-4 rounded-lg ${hasGameBan ? 'bg-red-900/20 border border-red-500/50' : 'bg-dark-bg'}`}>
            <p className="text-gray-400 text-sm">Game Bans</p>
            <p className={`text-2xl font-bold ${hasGameBan ? 'text-red-400' : 'text-green-400'}`}>
              {profile.bans.game_bans}
            </p>
          </div>

          <div className={`p-4 rounded-lg ${hasCommunityBan ? 'bg-red-900/20 border border-red-500/50' : 'bg-dark-bg'}`}>
            <p className="text-gray-400 text-sm">Community Ban</p>
            <p className={`text-sm font-semibold ${hasCommunityBan ? 'text-red-400' : 'text-green-400'}`}>
              {hasCommunityBan ? 'Banned' : 'Clean'}
            </p>
          </div>

          <div className={`p-4 rounded-lg ${hasTradeBan ? 'bg-red-900/20 border border-red-500/50' : 'bg-dark-bg'}`}>
            <p className="text-gray-400 text-sm">Trade Status</p>
            <p className={`text-sm font-semibold ${hasTradeBan ? 'text-red-400' : 'text-green-400'}`}>
              {profile.bans.trade_ban === 'none' || !profile.bans.trade_ban ? 'None' : profile.bans.trade_ban}
            </p>
          </div>
        </div>

        {profile.bans.days_since_last_ban !== null && profile.bans.days_since_last_ban !== undefined && (
          <div className="mt-4 p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-red-400 text-sm font-semibold">
              Last ban was {profile.bans.days_since_last_ban} days ago
            </p>
          </div>
        )}
      </div>

      {/* Recent Changes Alert */}
      {hasRecentChanges && (
        <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-4">
          <h3 className="text-yellow-400 font-semibold mb-2 flex items-center gap-2">
            <ExclamationTriangleIcon className="w-5 h-5" />
            Changes Detected Since Last Search
          </h3>
          <div className="space-y-2">
            {Object.entries(profile.changes).map(([key, change]) => (
              <div key={key} className="text-sm">
                <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}: </span>
                <span className="text-red-400 line-through">{String(change.old)}</span>
                {' → '}
                <span className="text-green-400">{String(change.new)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Statistics */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <ClockIcon className="w-5 h-5 text-primary-400" />
          Search Statistics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Total Searches</p>
            <p className="text-2xl font-bold text-white">{profile.search_stats.total_searches}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">First Searched</p>
            <p className="text-white">
              {formatDistanceToNow(new Date(profile.search_stats.first_searched), { addSuffix: true })}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Last Searched</p>
            <p className="text-white">
              {formatDistanceToNow(new Date(profile.search_stats.last_searched), { addSuffix: true })}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Last Searched By</p>
            <p className="text-white">{profile.search_stats.last_searched_by || 'Unknown'}</p>
          </div>
        </div>
      </div>

      {/* Related Templates */}
      {profile.related_templates.length > 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <DocumentTextIcon className="w-5 h-5 text-primary-400" />
            Related Refund Requests ({profile.related_templates.length})
          </h3>
          <div className="space-y-3">
            {profile.related_templates.map((template) => (
              <div key={template.id} className="p-4 bg-dark-bg rounded-lg border border-dark-border">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <p className="font-semibold text-white">Ticket #{template.ticket_number}</p>
                      <span className={`px-2 py-1 text-xs rounded ${
                        template.status === 'approved' ? 'bg-green-900/50 text-green-400' :
                        template.status === 'denied' ? 'bg-red-900/50 text-red-400' :
                        template.status === 'completed' ? 'bg-blue-900/50 text-blue-400' :
                        'bg-yellow-900/50 text-yellow-400'
                      }`}>
                        {template.status}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mt-1">IGN: {template.player_ign}</p>
                    <p className="text-gray-500 text-sm mt-1">{template.items_lost}</p>
                    <p className="text-gray-500 text-xs mt-2">
                      By {template.created_by} • {formatDistanceToNow(new Date(template.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search History */}
      {profile.search_history.length > 1 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <UserIcon className="w-5 h-5 text-primary-400" />
            Search History
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {profile.search_history.slice(0, 10).map((history, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
                <div className="flex-1">
                  <p className="text-white text-sm">{history.persona_name}</p>
                  <p className="text-gray-500 text-xs">
                    {format(new Date(history.searched_at), 'MMM d, yyyy h:mm a')} by {history.searched_by}
                  </p>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  {history.vac_bans > 0 && (
                    <span className="text-red-400">VAC: {history.vac_bans}</span>
                  )}
                  {history.game_bans > 0 && (
                    <span className="text-red-400">Game: {history.game_bans}</span>
                  )}
                  {Object.keys(history.changes).length > 0 && (
                    <span className="text-yellow-400 text-xs">Changed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
