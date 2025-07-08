/**
 * Simple toast notification utility
 */

export interface ToastOptions {
  title?: string;
  description?: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

class ToastManager {
  private toasts: Map<string, HTMLElement> = new Map();
  private toastContainer: HTMLElement | null = null;

  constructor() {
    this.createContainer();
  }

  private createContainer() {
    if (typeof window === 'undefined') return;
    
    this.toastContainer = document.createElement('div');
    this.toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
    document.body.appendChild(this.toastContainer);
  }

  private getIconForType(type: ToastOptions['type']) {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  }

  private getColorForType(type: ToastOptions['type']) {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  }

  show(options: ToastOptions) {
    if (!this.toastContainer) return;

    const id = Math.random().toString(36).substr(2, 9);
    const toast = document.createElement('div');
    
    const { title, description, type = 'info', duration = 5000 } = options;
    const icon = this.getIconForType(type);
    const colorClass = this.getColorForType(type);

    toast.className = `${colorClass} border rounded-lg p-4 shadow-lg max-w-sm transition-all duration-300 transform translate-x-full opacity-0`;
    toast.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="text-lg">${icon}</span>
        <div class="flex-1 min-w-0">
          ${title ? `<h4 class="font-medium text-sm mb-1">${title}</h4>` : ''}
          ${description ? `<p class="text-sm opacity-90">${description}</p>` : ''}
        </div>
        <button class="text-current opacity-50 hover:opacity-100 text-sm" onclick="this.parentElement.parentElement.remove()">
          ×
        </button>
      </div>
    `;

    this.toastContainer.appendChild(toast);
    this.toasts.set(id, toast);

    // Trigger animation
    setTimeout(() => {
      toast.classList.remove('translate-x-full', 'opacity-0');
    }, 100);

    // Auto remove
    setTimeout(() => {
      this.remove(id);
    }, duration);

    return id;
  }

  remove(id: string) {
    const toast = this.toasts.get(id);
    if (toast) {
      toast.classList.add('translate-x-full', 'opacity-0');
      setTimeout(() => {
        toast.remove();
        this.toasts.delete(id);
      }, 300);
    }
  }

  success(message: string, title?: string) {
    return this.show({
      title,
      description: message,
      type: 'success',
    });
  }

  error(message: string, title?: string) {
    return this.show({
      title,
      description: message,
      type: 'error',
    });
  }

  info(message: string, title?: string) {
    return this.show({
      title,
      description: message,
      type: 'info',
    });
  }

  warning(message: string, title?: string) {
    return this.show({
      title,
      description: message,
      type: 'warning',
    });
  }
}

// Export singleton instance
export const toast = new ToastManager(); 