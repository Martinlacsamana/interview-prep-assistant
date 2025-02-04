# RUBY - AI Interview Prep Assistant 🤖

An AI-powered Telegram bot that helps developers prepare for technical interviews through interactive practice, personalized feedback, and resource generation. Built with OpenAI's Assistant API, this bot provides comprehensive interview preparation tools and tracks progress over time.

## 🧠 Core Features

### 1. Interactive Practice & Learning
- Real-time coding problem generation
- Customizable difficulty levels (easy/medium/hard)
- Topic-specific practice sessions
- Instant feedback and explanations

### 2. Smart Tools

#### Technical Cheatsheet Generator
- Generates comprehensive technical cheatsheets
- Covers key concepts, patterns, and best practices
- Email delivery via SendGrid
- Markdown-formatted for readability

#### Practice Problem Generator
- Supports multiple programming topics
- Adjustable difficulty levels
- Includes problem constraints and examples
- Provides starter code and hints

#### Progress Analysis & Feedback
- Tracks interaction history in MongoDB
- Generates personalized feedback reports
- Identifies strengths and weaknesses
- Suggests focused study plans

## 🏗️ Architecture

### OpenAI Integration
- Uses Assistants API for natural conversations
- Function calling for specialized tools
- Context-aware responses
- Conversation history tracking

### Data Storage
- MongoDB for interaction storage
- Asynchronous operations with Motor
- Structured data for analysis
- Performance optimized queries

### Telegram Bot
- Webhook-based updates
- Async message handling
- Interactive command system
- Error handling and recovery

## 🛠️ Technology Stack

- **Backend Framework**: Flask + Uvicorn
- **Database**: MongoDB
- **AI**: OpenAI Assistants API
- **Bot Platform**: Telegram Bot API
- **Email Service**: SendGrid
- **Dependencies**: See `requirements.txt`

## 🤝 Bot Interactions

Users can:
1. Generate practice problems: "Give me a medium difficulty problem about binary trees"
2. Request cheatsheets: "Create a cheatsheet about system design"
3. Get progress feedback: "How am I doing with algorithmic problems?"
4. Ask technical questions: "Explain time complexity in binary search"

The bot maintains context and provides coherent, helpful responses while storing interactions for future analysis.
