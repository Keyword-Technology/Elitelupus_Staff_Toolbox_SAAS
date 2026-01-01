'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { rulesAPI } from '@/lib/api';
import {
  BookOpenIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  BriefcaseIcon,
  FolderIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  XMarkIcon,
  CheckIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface RuleCategory {
  id: number;
  name: string;
  description: string;
  order: number;
  icon: string;
  is_active: boolean;
  rules: Rule[];
  rule_count: number;
}

interface Rule {
  id: number;
  code: string;
  title: string;
  content: string;
  order: number;
  is_active: boolean;
  category: number;
  category_name?: string;
  created_at?: string;
  updated_at?: string;
}

interface JobAction {
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
  order: number;
  is_active: boolean;
}

type TabType = 'categories' | 'rules' | 'jobs';

export default function RulesManagePage() {
  const { user, hasMinRole } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('categories');
  const [loading, setLoading] = useState(true);
  const [accessDenied, setAccessDenied] = useState(false);

  // Data state
  const [categories, setCategories] = useState<RuleCategory[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [jobs, setJobs] = useState<JobAction[]>([]);
  
  // UI state
  const [expandedCategories, setExpandedCategories] = useState<number[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  // Modal state
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showJobModal, setShowJobModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<{type: string; id: number; name: string} | null>(null);

  // Edit state
  const [editingCategory, setEditingCategory] = useState<RuleCategory | null>(null);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [editingJob, setEditingJob] = useState<JobAction | null>(null);

  // Form state
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: '',
    order: 0,
    icon: '',
    is_active: true,
  });

  const [ruleForm, setRuleForm] = useState({
    category: 0,
    code: '',
    title: '',
    content: '',
    order: 0,
    is_active: true,
  });

  const [jobForm, setJobForm] = useState({
    job_name: '',
    category: '',
    can_raid: false,
    raid_note: '',
    can_steal: false,
    steal_note: '',
    can_mug: false,
    mug_note: '',
    can_kidnap: false,
    kidnap_note: '',
    can_base: false,
    base_note: '',
    can_have_printers: false,
    printers_note: '',
    additional_notes: '',
    order: 0,
    is_active: true,
  });

  // Check permissions (Manager+ required, priority <= 10)
  useEffect(() => {
    if (user && !hasMinRole(10)) {
      setAccessDenied(true);
      toast.error('You do not have permission to manage rules');
      router.push('/dashboard/rules');
      return;
    }
    if (user && hasMinRole(10)) {
      setAccessDenied(false);
    }
  }, [user, hasMinRole, router]);

  useEffect(() => {
    if (user && hasMinRole(10) && !accessDenied) {
      fetchData();
    }
  }, [activeTab, user, hasMinRole, accessDenied]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'categories' || activeTab === 'rules') {
        const res = await rulesAPI.manageCategories();
        const data = Array.isArray(res.data) ? res.data : res.data.results || [];
        setCategories(data);
      }
      if (activeTab === 'rules') {
        const res = await rulesAPI.manageRules(selectedCategory || undefined);
        const data = Array.isArray(res.data) ? res.data : res.data.results || [];
        setRules(data);
      }
      if (activeTab === 'jobs') {
        const res = await rulesAPI.manageJobs();
        const data = Array.isArray(res.data) ? res.data : res.data.results || [];
        setJobs(data);
      }
    } catch (error) {
      toast.error('Failed to load data');
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Toggle category expansion
  const toggleCategory = (id: number) => {
    setExpandedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  // Category handlers
  const openCategoryModal = (category?: RuleCategory) => {
    if (category) {
      setEditingCategory(category);
      setCategoryForm({
        name: category.name,
        description: category.description,
        order: category.order,
        icon: category.icon || '',
        is_active: category.is_active,
      });
    } else {
      setEditingCategory(null);
      setCategoryForm({
        name: '',
        description: '',
        order: categories.length * 10,
        icon: '',
        is_active: true,
      });
    }
    setShowCategoryModal(true);
  };

  const saveCategory = async () => {
    try {
      if (editingCategory) {
        await rulesAPI.updateCategory(editingCategory.id, categoryForm);
        toast.success('Category updated successfully');
      } else {
        await rulesAPI.createCategory(categoryForm);
        toast.success('Category created successfully');
      }
      setShowCategoryModal(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save category');
    }
  };

  const deleteCategory = async (id: number) => {
    try {
      await rulesAPI.deleteCategory(id);
      toast.success('Category deleted successfully');
      setShowDeleteConfirm(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete category');
    }
  };

  // Rule handlers
  const openRuleModal = (rule?: Rule, categoryId?: number) => {
    if (rule) {
      setEditingRule(rule);
      setRuleForm({
        category: rule.category,
        code: rule.code,
        title: rule.title,
        content: rule.content,
        order: rule.order,
        is_active: rule.is_active,
      });
    } else {
      setEditingRule(null);
      setRuleForm({
        category: categoryId || categories[0]?.id || 0,
        code: '',
        title: '',
        content: '',
        order: 0,
        is_active: true,
      });
    }
    setShowRuleModal(true);
  };

  const saveRule = async () => {
    try {
      if (editingRule) {
        await rulesAPI.updateRule(editingRule.id, ruleForm);
        toast.success('Rule updated successfully');
      } else {
        await rulesAPI.createRule(ruleForm);
        toast.success('Rule created successfully');
      }
      setShowRuleModal(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save rule');
    }
  };

  const deleteRule = async (id: number) => {
    try {
      await rulesAPI.deleteRule(id);
      toast.success('Rule deleted successfully');
      setShowDeleteConfirm(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete rule');
    }
  };

  // Job handlers
  const openJobModal = (job?: JobAction) => {
    if (job) {
      setEditingJob(job);
      setJobForm({
        job_name: job.job_name,
        category: job.category,
        can_raid: job.can_raid,
        raid_note: job.raid_note,
        can_steal: job.can_steal,
        steal_note: job.steal_note,
        can_mug: job.can_mug,
        mug_note: job.mug_note,
        can_kidnap: job.can_kidnap,
        kidnap_note: job.kidnap_note,
        can_base: job.can_base,
        base_note: job.base_note,
        can_have_printers: job.can_have_printers,
        printers_note: job.printers_note,
        additional_notes: job.additional_notes,
        order: job.order,
        is_active: job.is_active,
      });
    } else {
      setEditingJob(null);
      setJobForm({
        job_name: '',
        category: '',
        can_raid: false,
        raid_note: '',
        can_steal: false,
        steal_note: '',
        can_mug: false,
        mug_note: '',
        can_kidnap: false,
        kidnap_note: '',
        can_base: false,
        base_note: '',
        can_have_printers: false,
        printers_note: '',
        additional_notes: '',
        order: jobs.length * 10,
        is_active: true,
      });
    }
    setShowJobModal(true);
  };

  const saveJob = async () => {
    try {
      if (editingJob) {
        await rulesAPI.updateJob(editingJob.id, jobForm);
        toast.success('Job rule updated successfully');
      } else {
        await rulesAPI.createJob(jobForm);
        toast.success('Job rule created successfully');
      }
      setShowJobModal(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save job rule');
    }
  };

  const deleteJob = async (id: number) => {
    try {
      await rulesAPI.deleteJob(id);
      toast.success('Job rule deleted successfully');
      setShowDeleteConfirm(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete job rule');
    }
  };

  // Handle delete confirmation
  const handleDelete = () => {
    if (!showDeleteConfirm) return;
    const { type, id } = showDeleteConfirm;
    if (type === 'category') deleteCategory(id);
    else if (type === 'rule') deleteRule(id);
    else if (type === 'job') deleteJob(id);
  };

  if (accessDenied) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-white mb-2">Access Denied</h2>
          <p className="text-gray-400">You do not have permission to manage rules.</p>
          <Link href="/dashboard/rules" className="btn-primary mt-4 inline-block">
            Back to Rules
          </Link>
        </div>
      </div>
    );
  }

  if (loading && categories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rules Management</h1>
          <p className="text-gray-400 text-sm mt-1">
            Create and edit server rules (Manager+ only)
          </p>
        </div>
        <Link
          href="/dashboard/rules"
          className="text-primary-400 hover:text-primary-300 text-sm"
        >
          ← Back to Rules View
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-dark-border">
        <button
          onClick={() => setActiveTab('categories')}
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'categories'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <FolderIcon className="w-5 h-5 inline mr-2" />
          Categories
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'rules'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <DocumentTextIcon className="w-5 h-5 inline mr-2" />
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
          Job Rules
        </button>
      </div>

      {/* Categories Tab */}
      {activeTab === 'categories' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => openCategoryModal()}
              className="btn-primary flex items-center gap-2"
            >
              <PlusIcon className="w-5 h-5" />
              Add Category
            </button>
          </div>

          {categories.length === 0 ? (
            <div className="text-center py-12 bg-dark-card rounded-lg border border-dark-border">
              <FolderIcon className="w-12 h-12 mx-auto text-gray-500 mb-4" />
              <p className="text-gray-400">No categories yet. Create your first category.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {categories.map((category) => (
                <div
                  key={category.id}
                  className="bg-dark-card rounded-lg border border-dark-border overflow-hidden"
                >
                  <div className="p-4 flex items-center justify-between">
                    <button
                      onClick={() => toggleCategory(category.id)}
                      className="flex items-center gap-3 flex-1 text-left"
                    >
                      {expandedCategories.includes(category.id) ? (
                        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-white font-medium">{category.name}</h3>
                          {!category.is_active && (
                            <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                              Inactive
                            </span>
                          )}
                        </div>
                        <p className="text-gray-400 text-sm">
                          {category.rule_count || category.rules?.length || 0} rules • Order: {category.order}
                        </p>
                      </div>
                    </button>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openRuleModal(undefined, category.id)}
                        className="p-2 text-green-400 hover:bg-green-500/20 rounded-lg transition-colors"
                        title="Add rule to this category"
                      >
                        <PlusIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => openCategoryModal(category)}
                        className="p-2 text-gray-400 hover:bg-dark-bg rounded-lg transition-colors"
                        title="Edit category"
                      >
                        <PencilIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm({ type: 'category', id: category.id, name: category.name })}
                        className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                        title="Delete category"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {expandedCategories.includes(category.id) && category.rules?.length > 0 && (
                    <div className="border-t border-dark-border p-4 bg-dark-bg/50">
                      <div className="space-y-2">
                        {category.rules.map((rule) => (
                          <div
                            key={rule.id}
                            className="flex items-center justify-between p-3 bg-dark-card rounded-lg"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-primary-400 font-mono text-sm">
                                {rule.code}
                              </span>
                              <span className="text-white">{rule.title}</span>
                              {!rule.is_active && (
                                <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                                  Inactive
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => openRuleModal(rule)}
                                className="p-1.5 text-gray-400 hover:bg-dark-bg rounded transition-colors"
                              >
                                <PencilIcon className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setShowDeleteConfirm({ type: 'rule', id: rule.id, name: `${rule.code} - ${rule.title}` })}
                                className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                              >
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <select
                value={selectedCategory || ''}
                onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                className="input"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => openRuleModal()}
              className="btn-primary flex items-center gap-2"
            >
              <PlusIcon className="w-5 h-5" />
              Add Rule
            </button>
          </div>

          {rules.length === 0 ? (
            <div className="text-center py-12 bg-dark-card rounded-lg border border-dark-border">
              <DocumentTextIcon className="w-12 h-12 mx-auto text-gray-500 mb-4" />
              <p className="text-gray-400">No rules found. Create your first rule.</p>
            </div>
          ) : (
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-dark-bg">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Code</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Title</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Category</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Status</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-dark-bg/50">
                      <td className="px-4 py-3 text-primary-400 font-mono">{rule.code}</td>
                      <td className="px-4 py-3 text-white">{rule.title}</td>
                      <td className="px-4 py-3 text-gray-400">{rule.category_name}</td>
                      <td className="px-4 py-3">
                        {rule.is_active ? (
                          <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">
                            Active
                          </span>
                        ) : (
                          <span className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => openRuleModal(rule)}
                          className="p-1.5 text-gray-400 hover:bg-dark-bg rounded transition-colors"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm({ type: 'rule', id: rule.id, name: `${rule.code} - ${rule.title}` })}
                          className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors ml-2"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Jobs Tab */}
      {activeTab === 'jobs' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => openJobModal()}
              className="btn-primary flex items-center gap-2"
            >
              <PlusIcon className="w-5 h-5" />
              Add Job Rule
            </button>
          </div>

          {jobs.length === 0 ? (
            <div className="text-center py-12 bg-dark-card rounded-lg border border-dark-border">
              <BriefcaseIcon className="w-12 h-12 mx-auto text-gray-500 mb-4" />
              <p className="text-gray-400">No job rules yet. Create your first job rule.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className={`bg-dark-card rounded-lg border ${job.is_active ? 'border-dark-border' : 'border-red-500/30'} p-4`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-white font-medium">{job.job_name}</h3>
                      {job.category && (
                        <p className="text-xs text-gray-500">{job.category}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {!job.is_active && (
                        <EyeSlashIcon className="w-4 h-4 text-red-400" title="Inactive" />
                      )}
                      <button
                        onClick={() => openJobModal(job)}
                        className="p-1.5 text-gray-400 hover:bg-dark-bg rounded transition-colors"
                      >
                        <PencilIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm({ type: 'job', id: job.id, name: job.job_name })}
                        className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-1 text-xs">
                    <PermissionBadge label="Raid" allowed={job.can_raid} />
                    <PermissionBadge label="Steal" allowed={job.can_steal} />
                    <PermissionBadge label="Mug" allowed={job.can_mug} />
                    <PermissionBadge label="Kidnap" allowed={job.can_kidnap} />
                    <PermissionBadge label="Base" allowed={job.can_base} />
                    <PermissionBadge label="Printers" allowed={job.can_have_printers} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Category Modal */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-md">
            <div className="p-4 border-b border-dark-border flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                {editingCategory ? 'Edit Category' : 'New Category'}
              </h2>
              <button onClick={() => setShowCategoryModal(false)} className="text-gray-400 hover:text-white">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Name *</label>
                <input
                  type="text"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  className="input w-full"
                  placeholder="General Rules"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                <textarea
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                  className="input w-full h-24"
                  placeholder="Optional description..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Order</label>
                  <input
                    type="number"
                    value={categoryForm.order}
                    onChange={(e) => setCategoryForm({ ...categoryForm, order: parseInt(e.target.value) || 0 })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Icon (optional)</label>
                  <input
                    type="text"
                    value={categoryForm.icon}
                    onChange={(e) => setCategoryForm({ ...categoryForm, icon: e.target.value })}
                    className="input w-full"
                    placeholder="book"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="cat-active"
                  checked={categoryForm.is_active}
                  onChange={(e) => setCategoryForm({ ...categoryForm, is_active: e.target.checked })}
                  className="rounded border-dark-border bg-dark-bg text-primary-500"
                />
                <label htmlFor="cat-active" className="text-sm text-gray-400">Active (visible to users)</label>
              </div>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3">
              <button onClick={() => setShowCategoryModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={saveCategory} className="btn-primary">
                {editingCategory ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Modal */}
      {showRuleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-dark-border flex items-center justify-between sticky top-0 bg-dark-card">
              <h2 className="text-lg font-semibold text-white">
                {editingRule ? 'Edit Rule' : 'New Rule'}
              </h2>
              <button onClick={() => setShowRuleModal(false)} className="text-gray-400 hover:text-white">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Category *</label>
                <select
                  value={ruleForm.category}
                  onChange={(e) => setRuleForm({ ...ruleForm, category: Number(e.target.value) })}
                  className="input w-full"
                >
                  <option value="">Select a category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Code *</label>
                  <input
                    type="text"
                    value={ruleForm.code}
                    onChange={(e) => setRuleForm({ ...ruleForm, code: e.target.value })}
                    className="input w-full"
                    placeholder="1.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Order</label>
                  <input
                    type="number"
                    value={ruleForm.order}
                    onChange={(e) => setRuleForm({ ...ruleForm, order: parseInt(e.target.value) || 0 })}
                    className="input w-full"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Title *</label>
                <input
                  type="text"
                  value={ruleForm.title}
                  onChange={(e) => setRuleForm({ ...ruleForm, title: e.target.value })}
                  className="input w-full"
                  placeholder="Rule title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Content *</label>
                <textarea
                  value={ruleForm.content}
                  onChange={(e) => setRuleForm({ ...ruleForm, content: e.target.value })}
                  className="input w-full h-40"
                  placeholder="Rule content..."
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="rule-active"
                  checked={ruleForm.is_active}
                  onChange={(e) => setRuleForm({ ...ruleForm, is_active: e.target.checked })}
                  className="rounded border-dark-border bg-dark-bg text-primary-500"
                />
                <label htmlFor="rule-active" className="text-sm text-gray-400">Active (visible to users)</label>
              </div>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3 sticky bottom-0 bg-dark-card">
              <button onClick={() => setShowRuleModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={saveRule} className="btn-primary">
                {editingRule ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Job Modal */}
      {showJobModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-dark-border flex items-center justify-between sticky top-0 bg-dark-card">
              <h2 className="text-lg font-semibold text-white">
                {editingJob ? 'Edit Job Rule' : 'New Job Rule'}
              </h2>
              <button onClick={() => setShowJobModal(false)} className="text-gray-400 hover:text-white">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Job Name *</label>
                  <input
                    type="text"
                    value={jobForm.job_name}
                    onChange={(e) => setJobForm({ ...jobForm, job_name: e.target.value })}
                    className="input w-full"
                    placeholder="Thief"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Category</label>
                  <input
                    type="text"
                    value={jobForm.category}
                    onChange={(e) => setJobForm({ ...jobForm, category: e.target.value })}
                    className="input w-full"
                    placeholder="Criminals"
                  />
                </div>
              </div>

              <div className="border-t border-dark-border pt-4">
                <h3 className="text-sm font-medium text-gray-400 mb-3">Permissions</h3>
                <div className="space-y-4">
                  <PermissionRow
                    label="Can Raid"
                    checked={jobForm.can_raid}
                    onCheck={(v) => setJobForm({ ...jobForm, can_raid: v })}
                    note={jobForm.raid_note}
                    onNote={(v) => setJobForm({ ...jobForm, raid_note: v })}
                  />
                  <PermissionRow
                    label="Can Steal"
                    checked={jobForm.can_steal}
                    onCheck={(v) => setJobForm({ ...jobForm, can_steal: v })}
                    note={jobForm.steal_note}
                    onNote={(v) => setJobForm({ ...jobForm, steal_note: v })}
                  />
                  <PermissionRow
                    label="Can Mug"
                    checked={jobForm.can_mug}
                    onCheck={(v) => setJobForm({ ...jobForm, can_mug: v })}
                    note={jobForm.mug_note}
                    onNote={(v) => setJobForm({ ...jobForm, mug_note: v })}
                  />
                  <PermissionRow
                    label="Can Kidnap"
                    checked={jobForm.can_kidnap}
                    onCheck={(v) => setJobForm({ ...jobForm, can_kidnap: v })}
                    note={jobForm.kidnap_note}
                    onNote={(v) => setJobForm({ ...jobForm, kidnap_note: v })}
                  />
                  <PermissionRow
                    label="Can Base"
                    checked={jobForm.can_base}
                    onCheck={(v) => setJobForm({ ...jobForm, can_base: v })}
                    note={jobForm.base_note}
                    onNote={(v) => setJobForm({ ...jobForm, base_note: v })}
                  />
                  <PermissionRow
                    label="Can Have Printers"
                    checked={jobForm.can_have_printers}
                    onCheck={(v) => setJobForm({ ...jobForm, can_have_printers: v })}
                    note={jobForm.printers_note}
                    onNote={(v) => setJobForm({ ...jobForm, printers_note: v })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Additional Notes</label>
                <textarea
                  value={jobForm.additional_notes}
                  onChange={(e) => setJobForm({ ...jobForm, additional_notes: e.target.value })}
                  className="input w-full h-24"
                  placeholder="Any additional notes about this job..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Order</label>
                  <input
                    type="number"
                    value={jobForm.order}
                    onChange={(e) => setJobForm({ ...jobForm, order: parseInt(e.target.value) || 0 })}
                    className="input w-full"
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="job-active"
                    checked={jobForm.is_active}
                    onChange={(e) => setJobForm({ ...jobForm, is_active: e.target.checked })}
                    className="rounded border-dark-border bg-dark-bg text-primary-500"
                  />
                  <label htmlFor="job-active" className="text-sm text-gray-400">Active</label>
                </div>
              </div>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3 sticky bottom-0 bg-dark-card">
              <button onClick={() => setShowJobModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={saveJob} className="btn-primary">
                {editingJob ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-md">
            <div className="p-4 border-b border-dark-border">
              <h2 className="text-lg font-semibold text-white">Confirm Delete</h2>
            </div>
            <div className="p-4">
              <p className="text-gray-400">
                Are you sure you want to delete <span className="text-white font-medium">{showDeleteConfirm.name}</span>?
                {showDeleteConfirm.type === 'category' && (
                  <span className="block mt-2 text-yellow-400 text-sm">
                    Warning: This will also delete all rules in this category!
                  </span>
                )}
              </p>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3">
              <button onClick={() => setShowDeleteConfirm(null)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleDelete} className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper components
function PermissionBadge({ label, allowed }: { label: string; allowed: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded ${
        allowed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
      }`}
    >
      {allowed ? <CheckIcon className="w-3 h-3" /> : <XMarkIcon className="w-3 h-3" />}
      {label}
    </span>
  );
}

function PermissionRow({
  label,
  checked,
  onCheck,
  note,
  onNote,
}: {
  label: string;
  checked: boolean;
  onCheck: (v: boolean) => void;
  note: string;
  onNote: (v: string) => void;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex items-center gap-2 w-40">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheck(e.target.checked)}
          className="rounded border-dark-border bg-dark-bg text-primary-500"
        />
        <span className="text-sm text-white">{label}</span>
      </div>
      <input
        type="text"
        value={note}
        onChange={(e) => onNote(e.target.value)}
        className="input flex-1"
        placeholder="Note (optional)"
      />
    </div>
  );
}
