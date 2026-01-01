'use client';

import { useState, useEffect } from 'react';
import { rulesAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import {
  BookOpenIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  BriefcaseIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface RuleCategory {
  id: number;
  name: string;
  description: string;
  order: number;
  rules: Rule[];
}

interface Rule {
  id: number;
  code: string;
  title: string;
  content: string;
  order: number;
  is_active: boolean;
}

interface JobRule {
  id: number;
  job_name: string;
  category: string;
  can_raid: boolean;
  raid_note: string;
  can_steal: boolean;
  steal_note: string;
  can_mug: boolean;
  mug_note: string;
  can_kidnap: boolean;
  kidnap_note: string;
  can_base: boolean;
  base_note: string;
  can_have_printers: boolean;
  printers_note: string;
  additional_notes: string;
}

export default function RulesPage() {
  const { hasMinRole } = useAuth();
  const [categories, setCategories] = useState<RuleCategory[]>([]);
  const [jobRules, setJobRules] = useState<JobRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Rule[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<number[]>([]);
  const [activeTab, setActiveTab] = useState<'general' | 'jobs'>('general');
  const [searching, setSearching] = useState(false);

  // Check if user can manage rules (Manager+ = priority <= 10)
  const canManageRules = hasMinRole(10);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    console.log('searchResults state changed:', searchResults);
  }, [searchResults]);

  const fetchData = async () => {
    try {
      const [categoriesRes, jobsRes] = await Promise.all([
        rulesAPI.all(),
        rulesAPI.jobs(),
      ]);
      setCategories(categoriesRes.data);
      setJobRules(jobsRes.data.results || jobsRes.data);
    } catch (error) {
      toast.error('Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      console.log('Searching for:', searchQuery);
      const res = await rulesAPI.search(searchQuery);
      console.log('Raw API response:', res);
      console.log('Response data:', res.data);
      const results = Array.isArray(res.data) ? res.data : (res.data.results || []);
      console.log('Parsed results:', results);
      console.log('Results length:', results.length);
      setSearchResults(results);
      console.log('State updated with results');
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed');
    } finally {
      setSearching(false);
    }
  };

  const toggleCategory = (id: number) => {
    setExpandedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Manager Actions */}
      {canManageRules && (
        <div className="flex justify-end">
          <Link
            href="/dashboard/rules/manage"
            className="btn-primary flex items-center gap-2"
          >
            <Cog6ToothIcon className="w-5 h-5" />
            Manage Rules
          </Link>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-dark-border">
        <button
          onClick={() => setActiveTab('general')}
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'general'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <BookOpenIcon className="w-5 h-5 inline mr-2" />
          General Rules
        </button>
        <button
          onClick={() => setActiveTab('jobs')}
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'jobs'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <BriefcaseIcon className="w-5 h-5 inline mr-2" />
          Job-Specific Rules
        </button>
      </div>

      {/* Search */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search rules..."
              className="input w-full pl-10"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="btn-primary"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-400">
              Found {searchResults.length} results
            </h3>
            {searchResults.map((rule) => (
              <div
                key={rule.id}
                className="p-4 bg-dark-bg rounded-lg border border-dark-border"
              >
                <div className="flex items-start gap-3">
                  <span className="text-primary-400 font-mono font-medium text-sm">
                    {rule.code}
                  </span>
                  <div className="flex-1">
                    <h4 className="text-white font-medium">{rule.title}</h4>
                    <p className="text-gray-400 text-sm mt-1">{rule.content}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* General Rules Content */}
      {activeTab === 'general' && (
        <div className="space-y-4">
          {categories.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No rules available</p>
          ) : (
            categories.map((category) => (
              <div
                key={category.id}
                className="bg-dark-card rounded-lg border border-dark-border overflow-hidden"
              >
                <button
                  onClick={() => toggleCategory(category.id)}
                  className="w-full p-4 flex items-center justify-between text-left hover:bg-dark-bg transition-colors"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {category.name}
                    </h3>
                    {category.description && (
                      <p className="text-gray-400 text-sm mt-1">
                        {category.description}
                      </p>
                    )}
                  </div>
                  {expandedCategories.includes(category.id) ? (
                    <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                  )}
                </button>

                {expandedCategories.includes(category.id) && (
                  <div className="border-t border-dark-border p-4 space-y-4">
                    {category.rules?.length === 0 ? (
                      <p className="text-gray-500 text-sm">
                        No rules in this category
                      </p>
                    ) : (
                      category.rules?.map((rule) => (
                        <div
                          key={rule.id}
                          className="p-4 bg-dark-bg rounded-lg"
                        >
                          <div className="flex items-start gap-3">
                            <span className="text-primary-400 font-mono font-medium text-sm">
                              {rule.code}
                            </span>
                            <div className="flex-1">
                              <h4 className="text-white font-medium">
                                {rule.title}
                              </h4>
                              <p className="text-gray-400 text-sm mt-2">
                                {rule.content}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Job-Specific Rules Content */}
      {activeTab === 'jobs' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobRules.length === 0 ? (
            <p className="text-gray-500 text-center py-8 col-span-full">
              No job rules available
            </p>
          ) : (
            jobRules.map((job) => (
              <div
                key={job.id}
                className="bg-dark-card rounded-lg border border-dark-border p-4"
              >
                <h3 className="text-lg font-semibold text-white mb-2">
                  {job.job_name}
                </h3>
                
                {job.category && (
                  <p className="text-xs text-gray-500 mb-3">{job.category}</p>
                )}
                
                {/* Permissions Grid */}
                <div className="space-y-2 mb-3">
                  {/* Raid Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_raid
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_raid ? '✓' : '✗'} Raid
                    </span>
                    {job.raid_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.raid_note}
                      </span>
                    )}
                  </div>

                  {/* Steal Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_steal
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_steal ? '✓' : '✗'} Steal
                    </span>
                    {job.steal_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.steal_note}
                      </span>
                    )}
                  </div>

                  {/* Mug Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_mug
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_mug ? '✓' : '✗'} Mug
                    </span>
                    {job.mug_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.mug_note}
                      </span>
                    )}
                  </div>

                  {/* Kidnap Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_kidnap
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_kidnap ? '✓' : '✗'} Kidnap
                    </span>
                    {job.kidnap_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.kidnap_note}
                      </span>
                    )}
                  </div>

                  {/* Base Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_base
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_base ? '✓' : '✗'} Base
                    </span>
                    {job.base_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.base_note}
                      </span>
                    )}
                  </div>

                  {/* Printers Permission */}
                  <div className="flex items-start gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        job.can_have_printers
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {job.can_have_printers ? '✓' : '✗'} Printers
                    </span>
                    {job.printers_note && (
                      <span className="text-xs text-gray-400 flex-1">
                        {job.printers_note}
                      </span>
                    )}
                  </div>
                </div>

                {job.additional_notes && (
                  <div className="mt-3 pt-3 border-t border-dark-border">
                    <p className="text-yellow-400 text-sm">
                      <span className="font-medium">Note:</span>{' '}
                      {job.additional_notes}
                    </p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
