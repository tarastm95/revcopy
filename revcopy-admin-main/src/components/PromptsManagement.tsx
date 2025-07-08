/**
 * Prompts Management Component for RevCopy Admin Panel
 * 
 * Provides comprehensive prompt template management with:
 * - Real-time data from backend API
 * - CRUD operations (Create, Read, Update, Delete)
 * - Form validation and error handling
 * - Loading states and user feedback
 * - Template variables with clickable insertion
 * - Responsive design
 */

import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Trash2, Save, X, AlertCircle, Loader2, Copy, Hash } from 'lucide-react';
import { useForm, UseFormRegister, FieldError } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

/**
 * Prompt template validation schema
 */
const promptSchema = z.object({
  content: z.string().min(1, 'Content is required').min(10, 'Content must be at least 10 characters'),
  category: z.string().min(1, 'Category is required'),
  isActive: z.boolean().default(true),
});

type PromptFormData = z.infer<typeof promptSchema>;

interface PromptTemplate {
  id: number;
  content: string;
  category: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Essential template variables - simplified
 */
const TEMPLATE_VARIABLES = {
  'Essential Variables': [
    { variable: '{product_description}', description: 'Product description' },
    { variable: '{positive_reviews}', description: 'Positive customer reviews' },
    { variable: '{negative_reviews}', description: 'Negative customer reviews' },
    { variable: '{product_name}', description: 'Product name/title' },
    { variable: '{brand}', description: 'Brand name' },
    { variable: '{price}', description: 'Product price' },
  ],
};

/**
 * Example templates for different categories
 * These templates are optimized for the actual frontend use cases
 */
const EXAMPLE_TEMPLATES: Record<string, string> = {
  // Core frontend categories (PRIORITY)
  facebook_ad: "Create a compelling Facebook ad for {product_name} that highlights {positive_reviews} and addresses {negative_reviews}. Keep it under 125 characters with a clear call-to-action.",
  
  product_description: "Write a detailed product description for {product_name} based on {product_description}. Highlight benefits from {positive_reviews} and address concerns from {negative_reviews}. Include key features and specifications.",
  
  google_ad: "Create a Google ad with compelling headline (30 chars max) and description (90 chars max) for {product_name}. Highlight {positive_reviews} and include {price}. Focus on key benefits and include a strong CTA.",
  
  instagram_caption: "Write an engaging Instagram caption for {product_name} featuring {positive_reviews}. Use emojis, 3-5 relevant hashtags, and mention {price} if competitive. Keep it conversational and visual.",
  
  blog_article: "Write a comprehensive blog article about {product_name} based on {product_description}. Feature customer insights from {positive_reviews}, address concerns from {negative_reviews}, and provide detailed analysis.",
  
  product_comparison: "Create a product comparison analysis for {product_name}. Compare features, highlight competitive advantages from {positive_reviews}, address any concerns from {negative_reviews}, and include {price} value proposition.",
  
  faq: "Create frequently asked questions and answers for {product_name}. Base questions on common concerns from {negative_reviews} and highlight strengths from {positive_reviews}. Include pricing and feature questions.",
  
  email_campaign: "Create an email campaign for {product_name} featuring social proof from {positive_reviews}. Address common objections from {negative_reviews}, include {price} and compelling call-to-action. Make it personal and engaging.",
  
  // Additional templates
  instagram_post: "Write an engaging Instagram post for {product_name} featuring {positive_reviews}. Use emojis and 3-5 relevant hashtags. Mention the {price} if it's competitive.",
  
  google_search_ad: "Create a Google Search ad with headline (30 chars max) and description (90 chars max) for {product_name}. Highlight {positive_reviews} and include {price}.",
  
  email_subject: "Create an email subject line (50 chars max) for {product_name} that incorporates {positive_reviews} or mentions the {price}.",
  
  youtube_description: "Write a YouTube video description for {product_name} featuring {positive_reviews}. Include {price} and detailed {product_description}.",
  
  linkedin_post: "Create a professional LinkedIn post about {product_name} highlighting {positive_reviews}. Focus on business benefits and include {price} if relevant.",
  
  twitter_post: "Write a Twitter post (280 chars max) for {product_name} featuring {positive_reviews}. Include relevant hashtags and {price}.",
  
  blog_post: "Write a blog post introduction about {product_name} based on {product_description}. Feature {positive_reviews} and address {negative_reviews}.",
  
  landing_page: "Create landing page copy for {product_name} with compelling headline, benefits from {positive_reviews}, and address {negative_reviews}. Include {price}."
};

/**
 * Content-specific prompt categories - each is its own complete entity
 * These MUST match the exact backend categories that the frontend requests!
 */
const PROMPT_CATEGORIES = [
  // Core categories that frontend actually requests (PRIORITY)
  { value: 'facebook_ad', label: '📘 Facebook Ad', priority: true },
  { value: 'product_description', label: '📦 Product Description', priority: true },
  { value: 'google_ad', label: '🔍 Google Ad', priority: true },
  { value: 'instagram_caption', label: '📸 Instagram Caption', priority: true },
  { value: 'blog_article', label: '📝 Blog Article', priority: true },
  { value: 'product_comparison', label: '⚖️ Product Comparison', priority: true },
  { value: 'faq', label: '❓ FAQ', priority: true },
  { value: 'email_campaign', label: '📧 Email Campaign', priority: true },
  
  // Additional categories for extended functionality
  { value: 'instagram_post', label: 'Instagram Post' },
  { value: 'linkedin_post', label: 'LinkedIn Post' },
  { value: 'twitter_post', label: 'Twitter Post' },
  { value: 'instagram_story', label: 'Instagram Story' },
  { value: 'google_search_ad', label: 'Google Search Ad' },
  { value: 'google_display_ad', label: 'Google Display Ad' },
  { value: 'google_shopping_ad', label: 'Google Shopping Ad' },
  { value: 'product_title', label: 'Product Title' },
  { value: 'product_features', label: 'Product Features' },
  { value: 'product_benefits', label: 'Product Benefits' },
  { value: 'email_subject', label: 'Email Subject Line' },
  { value: 'newsletter', label: 'Newsletter' },
  { value: 'welcome_email', label: 'Welcome Email' },
  { value: 'landing_page', label: 'Landing Page' },
  { value: 'homepage_hero', label: 'Homepage Hero' },
  { value: 'about_us', label: 'About Us Page' },
  { value: 'blog_post', label: 'Blog Post' },
  { value: 'sales_copy', label: 'Sales Copy' },
  { value: 'press_release', label: 'Press Release' },
  { value: 'case_study', label: 'Case Study' },
  { value: 'testimonial', label: 'Customer Testimonial' },
  { value: 'category_description', label: 'Category Description' },
  { value: 'brand_story', label: 'Brand Story' },
  { value: 'shipping_policy', label: 'Shipping Policy' },
  { value: 'return_policy', label: 'Return Policy' },
  { value: 'faq_answer', label: 'FAQ Answer' },
  { value: 'help_article', label: 'Help Article' },
  { value: 'chatbot_response', label: 'Chatbot Response' },
  { value: 'youtube_description', label: 'YouTube Description' },
  { value: 'video_script', label: 'Video Script' },
  { value: 'podcast_description', label: 'Podcast Description' },
];

/**
 * Template Variables Component
 */
interface TemplateVariablesProps {
  onVariableClick: (variable: string) => void;
}

const TemplateVariables: React.FC<TemplateVariablesProps> = ({ onVariableClick }) => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>('Product Information');
  const { toast } = useToast();

  const handleVariableClick = (variable: string) => {
    onVariableClick(variable);
    navigator.clipboard.writeText(variable);
    toast({
      title: 'Variable Copied',
      description: `${variable} has been copied to clipboard and inserted`,
    });
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center mb-3">
        <Hash className="w-4 h-4 mr-2 text-indigo-600" />
        <h4 className="text-sm font-semibold text-gray-900">Template Variables</h4>
        <span className="text-xs text-gray-500 ml-2">(Click to insert)</span>
      </div>
      
      <div className="space-y-3">
        {Object.entries(TEMPLATE_VARIABLES).map(([category, variables]) => (
          <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedCategory(expandedCategory === category ? null : category)}
              className="w-full px-3 py-2 bg-white hover:bg-gray-50 text-left text-sm font-medium text-gray-700 border-b border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset"
            >
              <div className="flex items-center justify-between">
                <span>{category}</span>
                <span className="text-xs text-gray-500">
                  {expandedCategory === category ? '▼' : '▶'}
                </span>
              </div>
            </button>
            
            {expandedCategory === category && (
              <div className="bg-white p-3 space-y-2">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {variables.map(({ variable, description }) => (
                    <button
                      key={variable}
                      onClick={() => handleVariableClick(variable)}
                      className="group flex items-center justify-between p-2 text-left bg-gray-50 hover:bg-indigo-50 border border-gray-200 hover:border-indigo-300 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <div className="flex-1 min-w-0">
                        <code className="text-xs font-mono text-indigo-600 group-hover:text-indigo-700 block">
                          {variable}
                        </code>
                        <p className="text-xs text-gray-500 mt-1 truncate" title={description}>
                          {description}
                        </p>
                      </div>
                      <Copy className="w-3 h-3 text-gray-400 group-hover:text-indigo-500 ml-2 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-700">
          <strong>💡 Example:</strong> For Facebook Ad: "Create a compelling Facebook ad for &#123;product_name&#125; highlighting &#123;positive_reviews&#125; and addressing concerns from &#123;negative_reviews&#125;. Keep it under 125 characters."
        </p>
        <p className="text-xs text-blue-600 mt-1">
          Each category is tailored for specific content types with appropriate length limits and style requirements.
        </p>
      </div>
    </div>
  );
};

/**
 * Main Prompts Management Component
 */
const PromptsManagement: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [editingPrompt, setEditingPrompt] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  /**
   * Fetch prompt templates from backend
   */
  const {
    data: prompts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['prompt-templates'],
    queryFn: async () => {
      const response = await apiClient.getPromptTemplates();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch prompt templates');
      }
      return response.data || [];
    },
    retry: 3,
  });

  /**
   * Create new prompt template mutation
   */
  const createPromptMutation = useMutation({
    mutationFn: async (promptData: PromptFormData) => {
      // Ensure category is not empty
      const templateData = {
        content: promptData.content,
        category: promptData.category || 'facebook_ad', // Default fallback
        is_active: promptData.isActive,
      };
      
      const response = await apiClient.createPromptTemplate(templateData);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to create prompt template');
      }
      
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt-templates'] });
      setShowAddForm(false);
      toast({
        title: 'Success',
        description: 'Prompt template created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Update prompt template mutation
   */
  const updatePromptMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: PromptFormData }) => {
      const response = await apiClient.updatePromptTemplate(id, {
        content: data.content,
        category: data.category,
        is_active: data.isActive,
      });
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to update prompt template');
      }
      
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt-templates'] });
      // Don't exit edit mode automatically - let user continue editing
      toast({
        title: 'Success',
        description: 'Prompt template updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Delete prompt template mutation
   */
  const deletePromptMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.deletePromptTemplate(id);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete prompt template');
      }
      
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt-templates'] });
      toast({
        title: 'Success',
        description: 'Prompt template deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Handle delete with confirmation
   */
  const handleDelete = async (id: number): Promise<void> => {
    if (window.confirm(`Are you sure you want to delete this prompt template? This action cannot be undone.`)) {
      deletePromptMutation.mutate(id);
    }
  };

  /**
   * Handle retry on error
   */
  const handleRetry = (): void => {
    refetch();
  };

  /**
   * Render loading state
   */
  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Prompts Management</h1>
            <p className="text-gray-600 mt-2">Edit and manage AI prompts and responses</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-gray-600">Loading prompt templates...</span>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Prompts Management</h1>
            <p className="text-gray-600 mt-2">Edit and manage AI prompts and responses</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Failed to load prompt templates</h3>
              <p className="text-sm text-red-600 mt-1">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </p>
              <Button 
                onClick={handleRetry} 
                className="mt-3 bg-red-600 hover:bg-red-700"
                size="sm"
              >
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Prompts Management</h1>
          <p className="text-gray-600 mt-2">Edit and manage AI prompts and responses</p>
        </div>
        <Button 
          onClick={() => setShowAddForm(true)}
          className="bg-indigo-600 hover:bg-indigo-700"
          disabled={createPromptMutation.isPending}
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Prompt
        </Button>
      </div>

      {/* Priority Categories Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <div className="text-blue-600 text-2xl">💡</div>
          <div>
            <h3 className="text-sm font-medium text-blue-800 mb-2">Frontend Integration Status</h3>
            <p className="text-sm text-blue-700 mb-3">
              These categories with 📘 📦 🔍 📸 📝 ⚖️ ❓ 📧 icons are <strong>high priority</strong> - they're actively used by the frontend content generation.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">📘 Facebook Ad</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">📦 Product Description</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">🔍 Google Ad</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">📸 Instagram Caption</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">📝 Blog Article</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">⚖️ Product Comparison</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">❓ FAQ</span>
              <span className="bg-white px-2 py-1 rounded border border-blue-200 text-blue-800">📧 Email Campaign</span>
            </div>
          </div>
        </div>
      </div>

      {/* Add New Prompt Form */}
      {showAddForm && (
        <AddPromptForm
          onSubmit={(data) => createPromptMutation.mutate(data)}
          onCancel={() => setShowAddForm(false)}
          isLoading={createPromptMutation.isPending}
          categories={PROMPT_CATEGORIES}
        />
      )}

      {/* Prompts List */}
      <div className="space-y-4">
        {prompts.length === 0 ? (
          <div className="text-center py-12">
            <Edit className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No prompt templates</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new prompt template.</p>
          </div>
        ) : (
          prompts.map((prompt: PromptTemplate) => (
            <PromptCard
              key={prompt.id}
              prompt={prompt}
              isEditing={editingPrompt === prompt.id}
              onEdit={() => setEditingPrompt(prompt.id)}
              onSave={(data) => updatePromptMutation.mutate({ id: prompt.id, data })}
              onDelete={() => handleDelete(prompt.id)}
              onCancel={() => setEditingPrompt(null)}
              isLoading={updatePromptMutation.isPending}
              categories={PROMPT_CATEGORIES}
            />
          ))
        )}
      </div>
    </div>
  );
};

/**
 * Add Prompt Form Component
 */
interface AddPromptFormProps {
  onSubmit: (data: PromptFormData) => void;
  onCancel: () => void;
  isLoading: boolean;
  categories: Array<{ value: string; label: string }>;
}

const AddPromptForm: React.FC<AddPromptFormProps> = ({ onSubmit, onCancel, isLoading, categories }) => {
  const contentTextareaRef = useRef<HTMLTextAreaElement>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    setValue,
    watch,
  } = useForm<PromptFormData>({
    resolver: zodResolver(promptSchema),
    defaultValues: {
      content: '',
      category: 'facebook_ad',
      isActive: true,
    },
  });

  const currentContent = watch('content');
  const currentCategory = watch('category');

  const handleFormSubmit = (data: PromptFormData): void => {
    onSubmit(data);
    reset();
  };

  const handleVariableInsert = (variable: string): void => {
    const textarea = contentTextareaRef.current;
    if (textarea) {
      const startPos = textarea.selectionStart;
      const endPos = textarea.selectionEnd;
      const newContent = currentContent.substring(0, startPos) + variable + currentContent.substring(endPos);
      
      setValue('content', newContent);
      
      // Set cursor position after the inserted variable
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(startPos + variable.length, startPos + variable.length);
      }, 0);
    } else {
      // Fallback: append to end
      setValue('content', currentContent + variable);
    }
  };

  const handleUseTemplate = (): void => {
    const template = EXAMPLE_TEMPLATES[currentCategory];
    if (template) {
      setValue('content', template);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Prompt Template</h3>
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
          <select
            {...register('category')}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            {categories.map((category) => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
          )}
        </div>
        
        {/* Template Variables Section */}
        <TemplateVariables onVariableClick={handleVariableInsert} />
        
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">Content</label>
            {EXAMPLE_TEMPLATES[currentCategory] && (
              <Button
                type="button"
                onClick={handleUseTemplate}
                variant="outline"
                size="sm"
                className="text-xs"
              >
                Use Template Example
              </Button>
            )}
          </div>
          <textarea
            {...register('content')}
            ref={contentTextareaRef}
            rows={6}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono text-sm"
            placeholder={EXAMPLE_TEMPLATES[currentCategory] ? 
              `Template available for ${categories.find(c => c.value === currentCategory)?.label || currentCategory}...` : 
              "Enter prompt content using template variables above..."
            }
          />
          {errors.content && (
            <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <input
            {...register('isActive')}
            type="checkbox"
            id="isActive"
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <label htmlFor="isActive" className="text-sm font-medium text-gray-700">
            Active
          </label>
        </div>
        <div className="flex space-x-3">
          <Button 
            type="submit" 
            className="bg-green-600 hover:bg-green-700"
            disabled={!isValid || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Prompt
              </>
            )}
          </Button>
          <Button 
            type="button"
            onClick={onCancel} 
            variant="outline"
            disabled={isLoading}
          >
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
};

/**
 * Individual Prompt Card Component
 */
interface PromptCardProps {
  prompt: PromptTemplate;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (data: PromptFormData) => void;
  onDelete: () => void;
  onCancel: () => void;
  isLoading: boolean;
  categories: Array<{ value: string; label: string }>;
}

const PromptCard: React.FC<PromptCardProps> = ({ 
  prompt, 
  isEditing, 
  onEdit, 
  onSave, 
  onDelete, 
  onCancel, 
  isLoading,
  categories 
}) => {
  const editContentTextareaRef = useRef<HTMLTextAreaElement>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
    reset,
    trigger,
  } = useForm<PromptFormData>({
    resolver: zodResolver(promptSchema),
    mode: 'onChange',
    defaultValues: {
      content: prompt.content || '',
      category: prompt.category || 'facebook_ad',
      isActive: prompt.is_active !== undefined ? prompt.is_active : true,
    },
  });

  // Reset form when switching to edit mode
  useEffect(() => {
    if (isEditing) {
      const resetData = {
        content: prompt.content || '',
        category: prompt.category || 'facebook_ad',
        isActive: prompt.is_active !== undefined ? prompt.is_active : true,
      };
      
      // Reset the form with the data
      reset(resetData, { 
        keepErrors: false, 
        keepDirty: false, 
        keepIsSubmitted: false,
        keepTouched: false,
        keepIsValid: false,
        keepSubmitCount: false
      });
      
      // Trigger validation after reset
      setTimeout(() => {
        trigger();
      }, 50);
    }
      }, [isEditing, prompt, reset, trigger]);

  const currentEditContent = watch('content');
  const currentEditCategory = watch('category');

  const getCategoryLabel = (value: string): string => {
    // Handle empty or undefined categories
    if (!value || value.trim() === '') {
      return 'Uncategorized';
    }
    const category = categories.find(cat => cat.value === value);
    return category?.label || value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const handleEditVariableInsert = (variable: string): void => {
    const textarea = editContentTextareaRef.current;
    if (textarea) {
      const startPos = textarea.selectionStart;
      const endPos = textarea.selectionEnd;
      const newContent = currentEditContent.substring(0, startPos) + variable + currentEditContent.substring(endPos);
      
      setValue('content', newContent, { shouldValidate: true });
      
      // Set cursor position after the inserted variable
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(startPos + variable.length, startPos + variable.length);
      }, 0);
    } else {
      // Fallback: append to end
      setValue('content', currentEditContent + variable, { shouldValidate: true });
    }
  };

  const handleEditUseTemplate = (): void => {
    const template = EXAMPLE_TEMPLATES[currentEditCategory];
    if (template) {
      setValue('content', template, { shouldValidate: true });
    }
  };

  if (isEditing) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Edit Prompt Template</h4>
        <form onSubmit={handleSubmit(onSave)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              {...register('category')}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
            {errors.category && (
              <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
            )}
          </div>
          
          {/* Template Variables Section for Edit Form */}
          <TemplateVariables onVariableClick={handleEditVariableInsert} />
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Content</label>
              {EXAMPLE_TEMPLATES[currentEditCategory] && (
                <Button
                  type="button"
                  onClick={handleEditUseTemplate}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  Use Template Example
                </Button>
              )}
            </div>
            <textarea
              {...register('content', { 
                required: 'Content is required',
                minLength: { value: 10, message: 'Content must be at least 10 characters' }
              })}
              ref={editContentTextareaRef}
              value={currentEditContent || ''}
              onChange={(e) => {
                setValue('content', e.target.value, { shouldValidate: true });
              }}
              rows={6}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono text-sm"
              placeholder={EXAMPLE_TEMPLATES[currentEditCategory] ? 
                `Template available for ${categories.find(c => c.value === currentEditCategory)?.label || currentEditCategory}...` : 
                "Enter prompt content using template variables above..."
              }
            />
            {errors.content && (
              <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <input
              {...register('isActive')}
              type="checkbox"
              id={`isActive-${prompt.id}`}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor={`isActive-${prompt.id}`} className="text-sm font-medium text-gray-700">
              Active
            </label>
          </div>
          {/* Debug info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <h5 className="text-sm font-medium text-blue-800 mb-2">Debug Info:</h5>
            <div className="text-sm text-blue-600 space-y-1">
              <p><strong>Form Valid:</strong> {isValid ? 'Yes' : 'No'}</p>
              <p><strong>Content Length (watched):</strong> {currentEditContent?.length || 0} chars</p>
              <p><strong>Content Value:</strong> "{currentEditContent?.substring(0, 50) || 'Empty'}..."</p>
              <p><strong>Category:</strong> {currentEditCategory}</p>
              <p><strong>Active:</strong> {watch('isActive') ? 'Yes' : 'No'}</p>
              {Object.keys(errors).length > 0 && (
                <div>
                  <strong>Errors:</strong>
                  <ul className="ml-4 mt-1">
                    {Object.entries(errors).map(([field, error]) => (
                      <li key={field}>
                        {field}: {error?.message || 'Invalid'}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          <div className="flex space-x-3">
            <Button 
              type="submit"
              className="bg-green-600 hover:bg-green-700"
              disabled={!isValid || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
            <Button 
              type="button"
              onClick={handleSubmit((data) => {
                onSave(data);
                // Close edit mode after saving
                setTimeout(() => onCancel(), 300);
              })}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={!isValid || isLoading}
            >
              <Save className="w-4 h-4 mr-2" />
              Save & Close
            </Button>
            <Button 
              type="button"
              onClick={onCancel} 
              variant="outline"
              disabled={isLoading}
            >
              <X className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              {getCategoryLabel(prompt.category)}
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              prompt.is_active 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {prompt.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <p className="text-gray-600 text-sm line-clamp-3">{prompt.content}</p>
          <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
            <span>Created: {new Date(prompt.created_at).toLocaleDateString()}</span>
            <span>Updated: {new Date(prompt.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="flex space-x-2 ml-4">
          <Button 
            onClick={onEdit} 
            variant="outline" 
            size="sm"
            disabled={isLoading}
          >
            <Edit className="w-4 h-4" />
          </Button>
          <Button 
            onClick={onDelete} 
            variant="outline" 
            size="sm" 
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            disabled={isLoading}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PromptsManagement;
