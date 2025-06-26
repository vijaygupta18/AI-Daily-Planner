# 🤖 AI Daily Planner

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Transform your productivity with AI-powered intelligent daily planning**

An advanced AI-powered daily planner that uses **genetic algorithms** and **natural language processing** to create optimized schedules from your natural language task descriptions. Say goodbye to manual scheduling and hello to intelligent productivity!

![AI Daily Planner Demo](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=AI+Daily+Planner+Demo)

## ✨ Features

### 🧠 **AI-Powered Intelligence**
- **Natural Language Processing**: Just type "Review quarterly reports for 2 hours tomorrow morning" 
- **Smart Task Parsing**: Automatically extracts duration, priority, deadlines, and preferences
- **Genetic Algorithm Optimization**: Finds the optimal schedule arrangement for maximum productivity
- **Intelligent Conflict Resolution**: Automatically handles scheduling conflicts and constraints

### 📅 **Advanced Scheduling**
- **Dynamic Timeline**: Beautiful visual timeline with drag-and-drop functionality
- **Priority-Based Organization**: Color-coded priority system (🔥 High, ⭐ Medium, 📝 Low)
- **Deadline Management**: Never miss important deadlines with smart scheduling
- **Break Optimization**: Automatically schedules optimal break times

### 🎯 **Task Management**
- **Smart Completion Tracking**: Mark tasks complete with visual feedback and celebrations
- **Progress Analytics**: Track productivity trends and completion rates
- **Task Categories**: Organize by work, personal, urgent, or custom categories
- **Duration Estimation**: AI learns from your patterns to suggest realistic timeframes

### 📊 **Analytics & Insights**
- **Daily/Weekly Reports**: Comprehensive productivity analytics
- **Completion Rates**: Track your success patterns
- **Time Distribution**: Visualize how you spend your time
- **Productivity Trends**: Identify your most productive hours

### 🔄 **Integrations**
- **Google Calendar Sync**: Two-way synchronization with your existing calendar
- **PDF Export**: Professional schedule reports
- **Cloud Storage**: Automatic backup and sync across devices
- **API Integration**: Connect with other productivity tools

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** ([Download](https://python.org/downloads/))
- **Node.js 14+** (Optional, for advanced features)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-daily-planner.git
cd ai-daily-planner
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# The SQLite database will be created automatically on first run
# No additional setup required!
```

### 4. Start the Application

```bash
# Navigate to backend API directory
cd backend/api

# Start the Flask server
python app.py
```

### 5. Open in Browser

Visit **http://localhost:5001** in your web browser and start planning! 🎉

## 📖 How to Use

### **Step 1: Add Your First Task**
Type in natural language:
```
"Complete project proposal for 3 hours by Friday morning, high priority"
"Call dentist for 15 minutes sometime today"
"Gym workout for 1 hour in the evening, medium priority"
```

### **Step 2: Let AI Optimize**
Click **"Optimize Schedule"** and watch the AI:
- Parse your natural language
- Extract task details automatically
- Create an optimal timeline
- Handle conflicts intelligently

### **Step 3: Track Progress**
- ✅ Mark tasks complete with celebration animations
- 📊 View analytics and productivity insights
- 🔄 Adjust schedule as needed
- 📅 Sync with Google Calendar

## 🏗️ Project Architecture

```
AISchedule/
├── 🎨 frontend/           # Beautiful, responsive UI
│   ├── components/        # Reusable UI components  
│   ├── css/              # Modern CSS with animations
│   ├── js/               # Vanilla JavaScript modules
│   └── index.html        # Main application entry
├── 🧠 backend/           # AI-powered backend
│   ├── ai_service/       # Core AI algorithms
│   │   ├── genetic_scheduler.py    # Genetic algorithm optimization
│   │   └── nlp_parser.py          # Natural language processing
│   ├── api/              # RESTful API endpoints
│   │   └── app.py        # Flask application server
│   ├── models/           # Data models and database
│   │   └── database.py   # SQLite database management
│   └── utils/            # Utility services
│       ├── calendar_sync.py       # Google Calendar integration
│       └── report_generator.py    # PDF export functionality
├── 📊 database/          # SQLite database storage
├── 🧪 tests/            # Comprehensive test suite
└── 📚 docs/             # Additional documentation
```

## 🔧 Advanced Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Google Calendar API (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Database Configuration
DATABASE_URL=sqlite:///planner.db

# AI Configuration
NLP_MODEL=spacy_sm_en_core_web
GENETIC_POPULATION_SIZE=100
GENETIC_GENERATIONS=50
```

### Google Calendar Integration

1. **Enable Google Calendar API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Calendar API
   - Create credentials (OAuth 2.0)

2. **Configure Credentials**:
   - Download credentials JSON
   - Add client ID and secret to `.env`
   - Restart the application

3. **Authorize Access**:
   - Click "Connect Google Calendar" in settings
   - Follow OAuth flow
   - Enjoy two-way synchronization!

## 🎨 UI Features

### **Modern Design System**
- **Glassmorphism Effects**: Subtle transparency and blur effects
- **Smooth Animations**: 60fps transitions and micro-interactions
- **Dark/Light Themes**: Automatic system preference detection
- **Responsive Design**: Perfect on desktop, tablet, and mobile

### **Interactive Elements**
- **Drag & Drop**: Rearrange tasks with smooth animations
- **Toast Notifications**: Beautiful success/error feedback
- **Loading States**: Skeleton screens and progress indicators
- **Hover Effects**: Subtle depth and elevation changes

### **Accessibility**
- **WCAG 2.1 AA Compliant**: Full keyboard navigation
- **Screen Reader Support**: Proper ARIA labels and roles
- **High Contrast Mode**: Enhanced visibility options
- **Focus Management**: Clear focus indicators

## 🚀 Performance

- **⚡ Fast Loading**: Optimized assets and caching
- **📱 Mobile First**: Progressive Web App capabilities
- **🔄 Offline Support**: Works without internet connection
- **⚙️ Background Processing**: Non-blocking AI computations

## 🔒 Security & Privacy

- **🔐 Local Storage**: All data stored locally by default
- **🛡️ CSRF Protection**: Secure form submissions
- **🔒 Input Validation**: Sanitized user inputs
- **🎭 No Tracking**: Privacy-first approach

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-username/ai-daily-planner.git
cd ai-daily-planner

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start development server
python backend/api/app.py
```

## 📈 Roadmap

- [ ] **Mobile Apps**: Native iOS and Android applications
- [ ] **Team Collaboration**: Shared schedules and team planning
- [ ] **Advanced AI**: Machine learning for better predictions
- [ ] **Integrations**: Slack, Notion, Todoist, and more
- [ ] **Voice Commands**: "Hey AI, schedule my day"
- [ ] **Smart Notifications**: Proactive scheduling suggestions

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check if port 5001 is in use
lsof -i :5001

# Kill process if needed
kill -9 $(lsof -t -i:5001)

# Restart server
python backend/api/app.py
```

**Database errors:**
```bash
# Delete database and restart (loses data)
rm backend/api/planner.db
python backend/api/app.py
```

**Google Calendar not syncing:**
- Check credentials in `.env` file
- Verify API is enabled in Google Cloud Console
- Re-authorize in application settings

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for inspiration in AI-powered productivity
- **Genetic Algorithm Research** for optimization techniques
- **Natural Language Processing** community for NLP libraries
- **Open Source Community** for amazing tools and libraries

## 📞 Support

- 📧 **Email**: support@ai-daily-planner.com
- 💬 **Discord**: [Join our community](https://discord.gg/ai-planner)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/ai-daily-planner/issues)
- 📖 **Documentation**: [Full Docs](https://docs.ai-daily-planner.com)

---

<div align="center">

**Made with ❤️ by the AI Daily Planner Team**

[⭐ Star us on GitHub](https://github.com/your-username/ai-daily-planner) • [🐦 Follow on Twitter](https://twitter.com/ai_daily_planner) • [📧 Subscribe to Newsletter](https://newsletter.ai-daily-planner.com)

</div> 