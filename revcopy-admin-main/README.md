# RevCopy Admin Panel

A comprehensive administration interface for managing the RevCopy AI-powered content generation platform.

## 🚀 Overview

The RevCopy Admin Panel provides administrators with powerful tools to manage users, prompt templates, system settings, and monitor platform analytics. Built with React, TypeScript, and modern web technologies for a seamless management experience.

## ✨ Features

### 🔐 **Authentication & Security**
- Secure JWT-based authentication
- Role-based access control (Admin only)
- Automatic token refresh
- Secure logout and session management

### 📊 **Dashboard & Analytics**
- Real-time system statistics
- User growth metrics
- Content generation analytics
- Product analysis tracking
- System health monitoring

### 📝 **Prompt Template Management**
- Create and edit AI prompt templates
- Organize templates by category (Facebook Ads, Google Ads, Instagram, Email, etc.)
- Activate/deactivate templates
- Template performance tracking
- Content type management

### 👥 **User Management**
- View all registered users
- Filter users by status and role
- Update user account statuses
- Monitor user activity
- User registration analytics

### ⚙️ **System Settings**
- Configure AI provider settings
- Manage content generation parameters
- Rate limiting configuration
- Email and notification settings
- System feature flags

## 🛠️ Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **State Management**: TanStack React Query
- **Form Handling**: React Hook Form + Zod validation
- **Styling**: Tailwind CSS + Shadcn/ui components
- **Authentication**: JWT tokens with secure storage
- **Build Tool**: Vite
- **Package Manager**: npm

## 📋 Prerequisites

Before setting up the admin panel, ensure you have:

- **Node.js** >= 18.0.0
- **npm** >= 9.0.0
- **RevCopy Backend** running on `http://localhost:8000`

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd revcopy/admin
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Environment Configuration
Create a `.env` file in the admin directory:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=RevCopy Admin Panel
VITE_APP_VERSION=1.0.0
```

### 4. Start Development Server
```bash
npm run dev
```

The admin panel will be available at: **http://localhost:3001**

### 5. Build for Production
```bash
npm run build
```

## 🔑 Authentication

### Setup Requirements
1. Configure admin users in the backend database
2. Ensure users have the `admin` role assigned
3. Users must be verified and active
4. Update API endpoints for production URLs

### Login Process
- Use your actual admin credentials created in the backend
- Authentication uses JWT tokens with automatic refresh
- Invalid credentials will return authentication errors

## 📁 Project Structure

```
admin/
├── src/
│   ├── components/           # React components
│   │   ├── ui/              # Reusable UI components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── PromptsManagement.tsx
│   │   ├── UsersManagement.tsx
│   │   └── Sidebar.tsx      # Navigation sidebar
│   ├── pages/               # Page components
│   │   ├── Index.tsx        # Main admin page
│   │   ├── Login.tsx        # Authentication page
│   │   └── NotFound.tsx     # 404 page
│   ├── context/             # React contexts
│   │   └── AuthContext.tsx  # Authentication context
│   ├── lib/                 # Utilities and services
│   │   ├── api.ts           # API client
│   │   └── utils.ts         # Helper functions
│   ├── hooks/               # Custom React hooks
│   └── types/               # TypeScript type definitions
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── tailwind.config.ts       # Tailwind CSS configuration
├── vite.config.ts          # Vite build configuration
└── README.md               # This file
```

## 🔧 Configuration

### API Configuration
Update the API base URL in `src/lib/api.ts`:
```typescript
const API_CONFIG = {
  BASE_URL: 'http://localhost:8000', // Update for production
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};
```

### Routing Configuration
The admin panel uses React Router for navigation:
- `/` - Dashboard (protected)
- `/login` - Authentication page
- All routes require admin authentication

## 🎯 Usage Guide

### 1. **Dashboard**
- View system overview and key metrics
- Monitor user activity and growth
- Track content generation statistics
- Check system health status

### 2. **Prompt Management**
- **Create Templates**: Add new AI prompt templates
- **Edit Templates**: Modify existing prompts
- **Categories**: Organize by content type
- **Status**: Activate/deactivate templates

### 3. **User Management**
- **View Users**: Browse all registered users
- **Filter**: Filter by status, role, or search term
- **Manage**: Update user account statuses
- **Analytics**: Monitor user activity

### 4. **System Settings**
- **AI Providers**: Configure API keys and settings
- **Content Generation**: Set default parameters
- **Rate Limiting**: Configure usage limits
- **Notifications**: Email and alert settings

## 🔒 Security Features

### Authentication Security
- JWT tokens with expiration
- Automatic token refresh
- Secure token storage (localStorage with expiration)
- Protected routes with role validation

### API Security
- Bearer token authentication
- Request timeout protection
- Error handling and retry logic
- CORS configuration for admin domain

### Best Practices
- Input validation on all forms
- XSS protection through React's built-in escaping
- CSRF protection via API design
- Secure logout with token cleanup

## 🚦 API Endpoints

The admin panel communicates with the following backend endpoints:

### Authentication
- `POST /api/v1/auth/login` - Admin login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Token refresh

### Admin Operations
- `GET /api/v1/admin/dashboard/stats` - Dashboard statistics
- `GET /api/v1/admin/prompt-templates` - Get prompt templates
- `POST /api/v1/admin/prompt-templates` - Create template
- `PUT /api/v1/admin/prompt-templates/{id}` - Update template
- `DELETE /api/v1/admin/prompt-templates/{id}` - Delete template
- `GET /api/v1/admin/users` - Get users list
- `PUT /api/v1/admin/users/{id}/status` - Update user status

## 🐛 Troubleshooting

### Common Issues

#### 1. **Login Issues**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Test admin authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-admin@email.com","password":"your-password"}'
```

#### 2. **API Connection Issues**
```bash
# Check CORS configuration in backend
# Ensure admin panel URL is in allowed origins
```

#### 3. **Build Issues**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
npm run dev
```

#### 4. **Port Conflicts**
```bash
# Check what's running on port 3001
lsof -i :3001

# Kill conflicting processes
kill -9 <PID>
```

## 🔄 Development Workflow

### 1. **Development Mode**
```bash
npm run dev          # Start development server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### 2. **Testing**
```bash
npm run test         # Run unit tests
npm run test:coverage # Run tests with coverage
```

### 3. **Production Build**
```bash
npm run build        # Build for production
npm run preview      # Preview production build
```

## 📊 Monitoring & Analytics

### Performance Metrics
- Dashboard load times
- API response times
- User interaction tracking
- Error monitoring

### Health Checks
- API connectivity status
- Authentication service health
- Database connection status
- AI provider availability

## 🤝 Contributing

### Code Standards
- **TypeScript**: All code must be typed
- **ESLint**: Follow the configured rules
- **Prettier**: Auto-format code
- **Comments**: JSDoc for all public functions

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation
4. Submit PR with description

## 📞 Support

### Getting Help
- **Documentation**: Check this README first
- **Backend Issues**: Check backend logs at `/logs`
- **Frontend Issues**: Check browser console
- **API Issues**: Verify backend health endpoint

### Common Commands
```bash
# Start admin panel
npm run dev

# Check backend status
curl http://localhost:8000/health

# View logs
tail -f logs/admin.log

# Reset authentication
localStorage.clear()
```

## 🔐 Production Deployment

### Environment Setup
1. **Update API URLs** for production backend
2. **Configure HTTPS** for secure communication
3. **Set up monitoring** for health checks
4. **Configure logging** for error tracking

### Security Checklist
- [ ] HTTPS enabled
- [ ] Production API keys configured
- [ ] CORS properly configured
- [ ] Authentication endpoints secured
- [ ] Error messages sanitized
- [ ] Logging configured
- [ ] Monitoring alerts set up

## 📝 License

This project is part of the RevCopy platform. All rights reserved.

---

**RevCopy Admin Panel** - Powerful administration interface for AI-powered content generation platform.

For more information, visit the [main RevCopy documentation](../README.md).
