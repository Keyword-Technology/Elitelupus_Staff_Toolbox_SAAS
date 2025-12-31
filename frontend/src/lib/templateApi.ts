// Template API Functions

import { api } from './api';
import type {
  Template,
  RefundTemplate,
  BanExtensionTemplate,
  PlayerReportTemplate,
  StaffApplicationResponse,
  TemplateComment,
  SteamProfile,
} from '@/types/templates';

export const templateAPI = {
  // Steam Lookup
  steamLookup: async (steamId: string): Promise<SteamProfile> => {
    const response = await api.post('/templates/steam-lookup/', { steam_id: steamId });
    return response.data;
  },

  // Refund Templates
  getRefunds: async () => {
    const response = await api.get<RefundTemplate[]>('/templates/refunds/');
    return response.data;
  },

  createRefund: async (data: Partial<RefundTemplate>) => {
    const response = await api.post<RefundTemplate>('/templates/refunds/', data);
    return response.data;
  },

  updateRefund: async (id: number, data: Partial<RefundTemplate>) => {
    const response = await api.patch<RefundTemplate>(`/templates/refunds/${id}/`, data);
    return response.data;
  },

  deleteRefund: async (id: number) => {
    await api.delete(`/templates/refunds/${id}/`);
  },

  // Ban Extension Templates
  getBanExtensions: async () => {
    const response = await api.get<BanExtensionTemplate[]>('/templates/ban-extensions/');
    return response.data;
  },

  createBanExtension: async (data: Partial<BanExtensionTemplate>) => {
    const response = await api.post<BanExtensionTemplate>('/templates/ban-extensions/', data);
    return response.data;
  },

  updateBanExtension: async (id: number, data: Partial<BanExtensionTemplate>) => {
    const response = await api.patch<BanExtensionTemplate>(`/templates/ban-extensions/${id}/`, data);
    return response.data;
  },

  deleteBanExtension: async (id: number) => {
    await api.delete(`/templates/ban-extensions/${id}/`);
  },

  // Player Report Templates
  getPlayerReports: async () => {
    const response = await api.get<PlayerReportTemplate[]>('/templates/player-reports/');
    return response.data;
  },

  createPlayerReport: async (data: Partial<PlayerReportTemplate>) => {
    const response = await api.post<PlayerReportTemplate>('/templates/player-reports/', data);
    return response.data;
  },

  updatePlayerReport: async (id: number, data: Partial<PlayerReportTemplate>) => {
    const response = await api.patch<PlayerReportTemplate>(`/templates/player-reports/${id}/`, data);
    return response.data;
  },

  deletePlayerReport: async (id: number) => {
    await api.delete(`/templates/player-reports/${id}/`);
  },

  // Staff Application Responses
  getStaffApplications: async () => {
    const response = await api.get<StaffApplicationResponse[]>('/templates/staff-applications/');
    return response.data;
  },

  createStaffApplication: async (data: Partial<StaffApplicationResponse>) => {
    const response = await api.post<StaffApplicationResponse>('/templates/staff-applications/', data);
    return response.data;
  },

  updateStaffApplication: async (id: number, data: Partial<StaffApplicationResponse>) => {
    const response = await api.patch<StaffApplicationResponse>(`/templates/staff-applications/${id}/`, data);
    return response.data;
  },

  deleteStaffApplication: async (id: number) => {
    await api.delete(`/templates/staff-applications/${id}/`);
  },

  // Template Comments
  getComments: async (templateType: string, templateId: number) => {
    const response = await api.get<TemplateComment[]>(
      `/templates/comments/?template_type=${templateType}&template_id=${templateId}`
    );
    return response.data;
  },

  addComment: async (data: { template_type: string; template_id: number; comment: string }) => {
    const response = await api.post<TemplateComment>('/templates/comments/', data);
    return response.data;
  },

  deleteComment: async (id: number) => {
    await api.delete(`/templates/comments/${id}/`);
  },
};
