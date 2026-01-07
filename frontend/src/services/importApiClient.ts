// frontend/src/services/importApiClient.ts
/**
 * API Client for Data Import operations
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  FileUploadResponse,
  ImportMappingConfig,
  ImportPreviewResponse,
  ImportExecutionResponse,
  ImportTemplate,
  TemplateInfo,
  ImportExamples,
} from '../types/import';

class ImportApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1/import',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = this.extractErrorMessage(error);
        return Promise.reject(new Error(message));
      }
    );
  }

  /**
   * Get import template structure
   */
  async getTemplate(): Promise<TemplateInfo> {
    const response = await this.client.get<TemplateInfo>('/template');
    return response.data;
  }

  /**
   * Upload file for import
   */
  async uploadFile(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<FileUploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  /**
   * Generate preview of import
   */
  async generatePreview(config: ImportMappingConfig): Promise<ImportPreviewResponse> {
    const response = await this.client.post<ImportPreviewResponse>('/preview', config);
    return response.data;
  }

  /**
   * Execute import and create diagram
   */
  async executeImport(config: ImportMappingConfig): Promise<ImportExecutionResponse> {
    const response = await this.client.post<ImportExecutionResponse>('/execute', config);
    return response.data;
  }

  /**
   * Direct import from template
   */
  async directImport(
    template: ImportTemplate,
    diagramName: string,
    workspaceName: string
  ): Promise<ImportExecutionResponse> {
    const params = new URLSearchParams({
      diagram_name: diagramName,
      workspace_name: workspaceName,
    });

    const response = await this.client.post<ImportExecutionResponse>(
      `/direct?${params.toString()}`,
      template
    );
    return response.data;
  }

  /**
   * Delete temporary file
   */
  async deleteTempFile(fileId: string): Promise<void> {
    await this.client.delete(`/file/${fileId}`);
  }

  /**
   * Get example files and mappings
   */
  async getExamples(): Promise<ImportExamples> {
    const response = await this.client.get<ImportExamples>('/examples');
    return response.data;
  }

  /**
   * Validate mapping configuration
   */
  validateMappingConfig(config: ImportMappingConfig): string[] {
    const errors: string[] = [];

    if (!config.file_id) {
      errors.push('File ID is required');
    }

    if (!config.diagram_name?.trim()) {
      errors.push('Diagram name is required');
    }

    if (!config.workspace_name?.trim()) {
      errors.push('Workspace name is required');
    }

    if (!config.node_mappings?.length) {
      errors.push('At least one node mapping is required');
    }

    config.node_mappings?.forEach((mapping, index) => {
      if (!mapping.node_type) {
        errors.push(`Node mapping ${index + 1}: Node type is required`);
      }
      if (!mapping.label_column) {
        errors.push(`Node mapping ${index + 1}: Label column is required`);
      }
    });

    config.edge_mappings?.forEach((mapping, index) => {
      if (!mapping.edge_type) {
        errors.push(`Edge mapping ${index + 1}: Edge type is required`);
      }
      if (!mapping.source_column) {
        errors.push(`Edge mapping ${index + 1}: Source column is required`);
      }
      if (!mapping.target_column) {
        errors.push(`Edge mapping ${index + 1}: Target column is required`);
      }
    });

    return errors;
  }

  /**
   * Create default mapping config from file preview
   */
  createDefaultMappingConfig(
    fileId: string,
    filePreview: FileUploadResponse,
    diagramName: string,
    workspaceName: string = 'default'
  ): ImportMappingConfig {
    const detected = filePreview.detected_structure;

    const config: ImportMappingConfig = {
      file_id: fileId,
      diagram_name: diagramName,
      workspace_name: workspaceName,
      node_mappings: [],
      edge_mappings: [],
      auto_layout: true,
      layout_algorithm: 'hierarchical',
    };

    if (detected.recommended_node_mapping) {
      config.node_mappings.push({
        node_type: 'class',
        label_column: detected.recommended_node_mapping.label_column || '',
        id_column: detected.recommended_node_mapping.id_column,
      });
    }

    return config;
  }

  /**
   * Download JSON template
   */
  downloadJsonTemplate(): void {
    const template: ImportTemplate = {
      nodes: [
        {
          id: 'example_package',
          type: 'package',
          label: 'Example Package',
        },
        {
          id: 'example_class',
          type: 'class',
          label: 'ExampleClass',
          parent_package_id: 'example_package',
          attributes: [
            { name: 'id', type: 'UUID', visibility: '-' },
            { name: 'name', type: 'String', visibility: '+' },
          ],
          methods: [
            { name: 'getName', return_type: 'String', parameters: [], visibility: '+' },
          ],
        },
      ],
      edges: [],
    };

    this.downloadFile(
      JSON.stringify(template, null, 2),
      'import_template.json',
      'application/json'
    );
  }

  /**
   * Download CSV template
   */
  downloadCsvTemplate(): void {
    const csvContent = `id,type,label,attributes,methods
user,class,User,"id:UUID;username:String;email:String","login(password:String):boolean;logout():void"
account,class,Account,"id:UUID;balance:Decimal","deposit(amount:Decimal):void"`;

    this.downloadFile(csvContent, 'import_template.csv', 'text/csv');
  }

  /**
   * Helper to download files
   */
  private downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Extract error message from axios error
   */
  private extractErrorMessage(error: AxiosError): string {
    if (error.response?.data) {
      const data = error.response.data as any;
      return data.detail || data.message || 'An error occurred';
    }
    if (error.request) {
      return 'No response from server';
    }
    return error.message || 'An error occurred';
  }
}

export const importApiClient = new ImportApiClient();
export default importApiClient;